from randovania.dol_patching.assembler import ppc


def test_stw():
    assert ppc.stw(ppc.r31, 0x1c, ppc.r1) == [0x93, 0xe1, 0x00, 0x1c]


def test_stfs():
    assert ppc.lfs(ppc.f0, 0x1000, ppc.r2) == [192, 0, 16, 0]
