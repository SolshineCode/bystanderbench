// extract_resid: dump per-layer residual-stream ("l_out-<L>") pooled activations
// for a token sequence, using llama.cpp's ggml_backend_sched_eval_callback.
//
// This is a purpose-built reimplementation for the concealment-probe project.
// It is NOT the original Trial 2 v4 script (that used a different stack); it
// reproduces the activation-extraction step through llama.cpp only (safe path
// on this rig -- no HF transformers eager generate).
//
// Config via environment variables (to avoid fighting common_params_parse):
//   RESID_TOKENS_FILE  path to text file, one token id per line (already
//                      chat-templated + tokenized externally via llama-server
//                      /apply-template + /tokenize on the SAME gguf)
//   RESID_OUT          output path prefix; writes <prefix>.bin and <prefix>.json
//   RESID_POOL_START   int, global token index where the pooled "range" begins
//                      (e.g., start of final assistant response); default 0
//   RESID_POOL_END     int, exclusive end of pooled range; default = n_tokens
//   RESID_LAYERS       comma-separated layer indices, or "all" (default)
//   RESID_MANIFEST     alternative to RESID_TOKENS_FILE/RESID_OUT: path to a
//                      TSV file with lines "tokens_file<TAB>out_prefix<TAB>pool_start<TAB>pool_end".
//                      Processes all samples in one model load, clearing the
//                      KV/memory state between samples.
//
// Output .bin layout: float32, [n_layers_selected][3][d_model]
//   slot 0: mean over ALL positions
//   slot 1: mean over [POOL_START, POOL_END)
//   slot 2: last position's vector
// .json records layer ids, d_model, n_tokens, pool range for the loader.
//
// Standard llama.cpp args still apply (-m, -ngl, -c, -b, --tensor-split, ...).

#include "arg.h"
#include "common.h"
#include "log.h"
#include "llama.h"

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <map>
#include <set>
#include <string>
#include <vector>

struct resid_state {
    std::set<int>                          layers;      // selected layer ids; empty = all
    int                                    d_model = 0;
    long                                   pool_start = 0;
    long                                   pool_end   = -1;  // -1 = n_tokens
    long                                   n_tokens_total = 0;
    // per-layer position counter (tokens seen so far for that layer)
    std::map<int, long>                    pos_seen;
    // per-layer accumulators
    std::map<int, std::vector<double>>     sum_all;
    std::map<int, std::vector<double>>     sum_range;
    std::map<int, long>                    cnt_range;
    std::map<int, std::vector<float>>      last_vec;
    std::vector<uint8_t>                   buf;         // staging for device tensors
};

static bool parse_layer_name(const char * name, int * layer_out) {
    // matches "l_out-<int>" exactly
    if (strncmp(name, "l_out-", 6) != 0) return false;
    char * end = nullptr;
    long l = strtol(name + 6, &end, 10);
    if (end == name + 6 || *end != '\0') return false;
    *layer_out = (int) l;
    return true;
}

static bool cb_resid(struct ggml_tensor * t, bool ask, void * user_data) {
    auto * st = (resid_state *) user_data;

    int layer = -1;
    const bool is_resid = parse_layer_name(t->name, &layer) &&
                          (st->layers.empty() || st->layers.count(layer));

    if (ask) {
        return is_resid;   // only observe residual-stream tensors we care about
    }
    if (!is_resid) {
        return true;
    }

    GGML_ASSERT(t->type == GGML_TYPE_F32 && "expected f32 residual tensor");

    const int64_t d = t->ne[0];
    const int64_t n = t->ne[1];       // tokens in this ubatch
    if (st->d_model == 0) st->d_model = (int) d;
    GGML_ASSERT((int) d == st->d_model);

    const uint8_t * data;
    const bool is_host = t->buffer && ggml_backend_buffer_is_host(t->buffer);
    if (is_host) {
        data = (const uint8_t *) t->data;
    } else {
        size_t nbytes = ggml_nbytes(t);
        st->buf.resize(nbytes);
        ggml_backend_tensor_get(t, st->buf.data(), 0, nbytes);
        data = st->buf.data();
    }

    auto & sa = st->sum_all[layer];
    auto & sr = st->sum_range[layer];
    auto & lv = st->last_vec[layer];
    if (sa.empty()) { sa.assign(d, 0.0); sr.assign(d, 0.0); lv.assign(d, 0.0f); st->cnt_range[layer] = 0; st->pos_seen[layer] = 0; }

    const long pe = st->pool_end < 0 ? st->n_tokens_total : st->pool_end;

    for (int64_t j = 0; j < n; ++j) {
        const long gpos = st->pos_seen[layer] + j;   // global position
        const float * row = (const float *) (data + j * t->nb[1]);
        const bool in_range = gpos >= st->pool_start && gpos < pe;
        for (int64_t i = 0; i < d; ++i) {
            sa[i] += row[i];
            if (in_range) sr[i] += row[i];
        }
        if (in_range) st->cnt_range[layer]++;
        if (gpos == st->n_tokens_total - 1) {
            memcpy(lv.data(), row, d * sizeof(float));
        }
    }
    st->pos_seen[layer] += n;
    return true;
}

static bool process_sample(llama_context * ctx, resid_state & st, int n_batch,
                           const std::string & tokens_file, const std::string & out_prefix,
                           long pool_start, long pool_end) {
    // reset per-sample state (keep layer selection)
    st.pos_seen.clear(); st.sum_all.clear(); st.sum_range.clear();
    st.cnt_range.clear(); st.last_vec.clear();
    st.d_model = 0;
    st.pool_start = pool_start;
    st.pool_end   = pool_end;

    std::vector<llama_token> tokens;
    {
        std::ifstream fin(tokens_file);
        if (!fin) { LOG_ERR("cannot open tokens file %s\n", tokens_file.c_str()); return false; }
        long v;
        while (fin >> v) tokens.push_back((llama_token) v);
    }
    if (tokens.empty()) { LOG_ERR("no tokens in %s\n", tokens_file.c_str()); return false; }
    st.n_tokens_total = (long) tokens.size();
    LOG_INF("sample %s: n_tokens = %zu, pool = [%ld, %ld)\n", out_prefix.c_str(), tokens.size(),
            st.pool_start, st.pool_end < 0 ? st.n_tokens_total : st.pool_end);

    if ((long) tokens.size() > (long) llama_n_ctx(ctx)) {
        LOG_ERR("sequence (%zu) exceeds n_ctx (%d) -- skipping %s\n",
                tokens.size(), llama_n_ctx(ctx), out_prefix.c_str());
        return false;
    }

    llama_memory_clear(llama_get_memory(ctx), true);

    for (size_t off = 0; off < tokens.size(); off += n_batch) {
        int n = (int) std::min((size_t) n_batch, tokens.size() - off);
        llama_batch batch = llama_batch_init(n, 0, 1);
        for (int i = 0; i < n; ++i) {
            batch.token[batch.n_tokens]     = tokens[off + i];
            batch.pos[batch.n_tokens]       = (llama_pos) (off + i);
            batch.n_seq_id[batch.n_tokens]  = 1;
            batch.seq_id[batch.n_tokens][0] = 0;
            batch.logits[batch.n_tokens]    = false;
            batch.n_tokens++;
        }
        if (llama_decode(ctx, batch)) {
            LOG_ERR("llama_decode failed at offset %zu\n", off);
            llama_batch_free(batch);
            return false;
        }
        llama_batch_free(batch);
    }

    std::vector<int> layer_ids;
    for (auto & kv : st.sum_all) layer_ids.push_back(kv.first);

    const int d = st.d_model;
    std::string bin_path = out_prefix + ".bin";
    std::ofstream fo(bin_path, std::ios::binary);
    for (int L : layer_ids) {
        std::vector<float> row(3 * d);
        long n_all = st.pos_seen[L];
        long n_rng = st.cnt_range[L];
        for (int i = 0; i < d; ++i) {
            row[i]         = (float) (st.sum_all[L][i] / std::max(1L, n_all));
            row[d + i]     = (float) (st.sum_range[L][i] / std::max(1L, n_rng));
            row[2 * d + i] = st.last_vec[L][i];
        }
        fo.write((const char *) row.data(), row.size() * sizeof(float));
        if (n_all != st.n_tokens_total) {
            LOG_ERR("WARNING: layer %d saw %ld tokens, expected %ld\n", L, n_all, st.n_tokens_total);
        }
    }
    fo.close();

    std::ofstream fj(out_prefix + ".json");
    fj << "{\"d_model\":" << d << ",\"n_tokens\":" << st.n_tokens_total
       << ",\"pool_start\":" << st.pool_start
       << ",\"pool_end\":" << (st.pool_end < 0 ? st.n_tokens_total : st.pool_end)
       << ",\"pool_count\":" << (layer_ids.empty() ? 0 : st.cnt_range[layer_ids[0]])
       << ",\"slots\":[\"mean_all\",\"mean_range\",\"last\"],\"layers\":[";
    for (size_t i = 0; i < layer_ids.size(); ++i) fj << (i ? "," : "") << layer_ids[i];
    fj << "]}\n";
    fj.close();

    LOG_INF("wrote %s (%zu layers x 3 x %d f32)\n", bin_path.c_str(), layer_ids.size(), d);
    return true;
}

int main(int argc, char ** argv) {
    common_params params;
    common_init();
    if (!common_params_parse(argc, argv, params, LLAMA_EXAMPLE_COMMON)) {
        return 1;
    }

    const char * manifest    = getenv("RESID_MANIFEST");
    const char * tokens_file = getenv("RESID_TOKENS_FILE");
    const char * out_prefix  = getenv("RESID_OUT");
    if (!manifest && (!tokens_file || !out_prefix)) {
        LOG_ERR("need RESID_MANIFEST or RESID_TOKENS_FILE+RESID_OUT\n");
        return 1;
    }

    resid_state st;
    if (const char * s = getenv("RESID_LAYERS")) {
        if (strcmp(s, "all") != 0) {
            std::string str(s); size_t p = 0;
            while (p < str.size()) {
                size_t q = str.find(',', p);
                if (q == std::string::npos) q = str.size();
                st.layers.insert(atoi(str.substr(p, q - p).c_str()));
                p = q + 1;
            }
        }
    }

    params.cb_eval           = cb_resid;
    params.cb_eval_user_data = &st;
    params.warmup            = false;

    auto llama_init = common_init_from_params(params);
    auto * model = llama_init->model();
    auto * ctx   = llama_init->context();
    if (!model || !ctx) { LOG_ERR("init failed\n"); return 1; }

    int n_ok = 0, n_fail = 0;
    if (manifest) {
        std::ifstream fm(manifest);
        if (!fm) { LOG_ERR("cannot open manifest %s\n", manifest); return 1; }
        std::string line;
        while (std::getline(fm, line)) {
            if (line.empty() || line[0] == '#') continue;
            std::vector<std::string> parts;
            size_t p = 0;
            while (p <= line.size()) {
                size_t q = line.find('\t', p);
                if (q == std::string::npos) { parts.push_back(line.substr(p)); break; }
                parts.push_back(line.substr(p, q - p));
                p = q + 1;
            }
            if (parts.size() < 4) { LOG_ERR("bad manifest line: %s\n", line.c_str()); n_fail++; continue; }
            bool ok = process_sample(ctx, st, params.n_batch, parts[0], parts[1],
                                     atol(parts[2].c_str()), atol(parts[3].c_str()));
            (ok ? n_ok : n_fail)++;
        }
    } else {
        long ps = 0, pe = -1;
        if (const char * s = getenv("RESID_POOL_START")) ps = atol(s);
        if (const char * s = getenv("RESID_POOL_END"))   pe = atol(s);
        bool ok = process_sample(ctx, st, params.n_batch, tokens_file, out_prefix, ps, pe);
        (ok ? n_ok : n_fail)++;
    }

    LOG_INF("done: %d ok, %d failed\n", n_ok, n_fail);
    llama_backend_free();
    return n_fail > 0 && n_ok == 0 ? 1 : 0;
}

// BUILD (recorded 2026-09-05, after the original command went unrecorded):
//   against the primary checkout (~/llama.cpp, arch set incl. olmo2/nemotron_h_moe):
//     see existing binary `extract_resid`
//   against ~/llama.cpp-new (c457e3b+, adds cohere2moe for North-Mini):
//     cd ~/llama.cpp-new && cmake --build build --target llama-common -j6
//     g++ -O2 -std=c++17 <this file> -I include -I ggml/include -I common -I vendor \
//       -Lbuild/bin -lllama-common -lllama -lggml -lggml-base \
//       -Wl,-rpath,/home/darkstar/llama.cpp-new/build/bin -o extract_resid_new
//   Verified 2026-09-05: both binaries produce bit-identical activations on the
//   same GGUF+tokens (Olmo-3-7B-Instruct Q4_K_M, layer 4, 30 tokens, CPU).
