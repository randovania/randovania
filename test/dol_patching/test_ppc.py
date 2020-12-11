from randovania.dol_patching.assembler import ppc


def test_stw():
    assert list(ppc.stw(ppc.r31, 0x1c, ppc.r1)) == [0x93, 0xe1, 0x00, 0x1c]


def test_stfs():
    assert list(ppc.lfs(ppc.f0, 0x1000, ppc.r2)) == [192, 0, 16, 0]


def test_addi():
    assert list(ppc.addi(ppc.r3, ppc.r1, 0x8)) == [0x38, 0x61, 0x00, 0x08]


def test_or():
    assert list(ppc.or_(ppc.r31, ppc.r3, ppc.r3)) == []
