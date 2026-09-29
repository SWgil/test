"""FIDES 독자 격자(기밀성만)와 ChainCaps 예산 격자의 동형성 확인.

사용법 (두 저장소를 나란히 체크아웃한 뒤):
    git clone https://github.com/microsoft/fides
    git clone https://github.com/Jxcup/chaincaps-code
    PYTHONPATH=chaincaps-code FIDES_NB=fides/Tutorial.ipynb python3 fides-chaincaps-isomorphism.py

독자 집합 R 을 예산 {send_email(r) | r in R} 로 옮기면
FIDES 의 join(독자 교집합) 과 ChainCaps 의 meet(싱크 교집합) 이 일치하고,
유출 검사(P-F: readers ⊇ recipient  대  Req ∈ budget) 도 같은 판단을 낸다.
"""
import itertools, json, os
nb = json.load(open(os.environ.get("FIDES_NB", "fides/Tutorial.ipynb")))
exec("".join(nb["cells"][21]["source"]))          # FIDES 노트북 CELL 21: Lattice 클래스들
from chaincaps.core.budget import Budget, SinkPrivilege, SinkType as S

U = frozenset({"alice@corp.com", "bob@corp.com", "eve@ext.com"})
def readers(rs):  # FIDES 기밀성 라벨: 독자 집합의 역-멱집합 격자 (CELL 25 readers_label 과 동일)
    return InverseLattice(PowersetLattice(frozenset(rs), U))
def budget(rs):   # ChainCaps 예산: 같은 독자 집합을 send_email 싱크로 표현
    return Budget.from_sinks(*[SinkPrivilege(S.SEND_EMAIL, r) for r in rs])

subsets = [frozenset(c) for n in range(len(U) + 1) for c in itertools.combinations(U, n)]
ok = all(readers(A).join(readers(B)).inner.subset
         == {p.scope for p in budget(A).meet(budget(B)).privileges}
         for A, B in itertools.product(subsets, repeat=2))
print(f"join == meet for all {len(subsets)**2} subset pairs:", ok)

doc = readers({"alice@corp.com", "bob@corp.com"})
for r in U:
    f = doc <= readers({r})                                              # P-F: readers ⊇ {r}
    c = budget({"alice@corp.com", "bob@corp.com"}).authorizes(SinkPrivilege(S.SEND_EMAIL, r))
    print(f"  send to {r:16s} FIDES P-F={f!s:5} ChainCaps={c!s:5} same={f == c}")

print("scope hierarchy (ChainCaps only): @corp.com subsumes bob@corp.com ->",
      budget({"@corp.com"}).authorizes(SinkPrivilege(S.SEND_EMAIL, "bob@corp.com")))
