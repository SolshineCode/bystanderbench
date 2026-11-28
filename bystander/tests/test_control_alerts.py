import importlib.util, csv
from pathlib import Path
_p = Path(__file__).resolve().parents[1] / "control_alerts.py"
_s = importlib.util.spec_from_file_location("control_alerts", _p)
ca = importlib.util.module_from_spec(_s); _s.loader.exec_module(ca)


def test_kappa_perfect_and_chance():
    assert ca.kappa(list("MFMF"), list("MFMF")) == 1.0
    assert abs(ca.kappa(list("MMFF"), list("MFMF"))) < 1e-9      # agreement no better than chance


def test_tally_counts_agreed_and_disagreements(tmp_path):
    key = tmp_path / "k.csv"; key.write_text("id,model,mode,sample,epoch\na,m1,t,s,1\nb,m1,t,s,2\nc,m2,t,s,1\n")
    la = tmp_path / "a.csv"; la.write_text("id,label\na,M\nb,F\nc,F\n")
    lb = tmp_path / "b.csv"; lb.write_text("id,label\na,M\nb,M\nc,F\n")
    out = tmp_path / "o.json"
    class A: pass
    a = A(); a.key, a.labels_a, a.labels_b, a.out = str(key), str(la), str(lb), str(out)
    ca.cmd_tally(a)
    import json; r = json.load(open(out))
    assert r["disagreements"] == ["b"] and r["models"]["m1"] == {"M": 1, "disagree": 1} and r["models"]["m2"] == {"F": 1}
