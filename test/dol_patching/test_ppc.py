from randovania.dol_patching.assembler import ppc


def test_instruction_iter():
    assert list(ppc.Instruction(1234).bytes_for(0)) == [0x00, 0x00, 0x04, 0xD2]


def test_instruction_eq():
    assert ppc.Instruction(1234) == ppc.Instruction(1234)


def test_instruction_with_label():
    instruction = ppc.Instruction(1234)
    assert instruction.label is None

    with_label = instruction.with_label("foobar")
    assert instruction is with_label
    assert instruction.label == "foobar"


def test_stw():
    assert list(ppc.stw(ppc.r31, 0x1c, ppc.r1).bytes_for(0)) == [0x93, 0xe1, 0x00, 0x1c]


def test_stfs():
    assert list(ppc.stfs(ppc.f0, 0x1000, ppc.r2).bytes_for(0)) == [208, 2, 16, 0]


def test_lfs():
    assert list(ppc.lfs(ppc.f0, (0x8041a4a8 - 0x804223c0), ppc.r2).bytes_for(0)) == [0xc0, 0x02, 0x80, 0xe8]


def test_addi():
    assert list(ppc.addi(ppc.r3, ppc.r1, 0x8).bytes_for(0)) == [0x38, 0x61, 0x00, 0x08]


def test_or():
    assert list(ppc.or_(ppc.r31, ppc.r3, ppc.r3).bytes_for(0)) == [124, 127, 27, 120]


def test_lmw():
    assert list(ppc.lmw(ppc.r25, 0x774, ppc.r25).bytes_for(0)) == [187, 57, 7, 116]


def test_lwz():
    assert list(ppc.lwz(ppc.r10, 0x774, ppc.r25).bytes_for(0)) == [0x81, 0x59, 0x07, 0x74]


def test_lbz():
    assert list(ppc.lbz(ppc.r4, 0x2, ppc.r3).bytes_for(0)) == [0x88, 0x83, 0x00, 0x02]


def test_cmpwi_a():
    assert list(ppc.cmpwi(ppc.r30, 0).bytes_for(0)) == [0x2c, 0x1e, 0x00, 0x00]


def test_cmpwi_b():
    assert list(ppc.cmpwi(ppc.r4, -1).bytes_for(0)) == [0x2c, 0x04, 0xFF, 0xFF]


def test_b():
    assert list(ppc.b(0x80085760).bytes_for(0x80085760 + 0x9C)) == [0x4b, 0xff, 0xff, 0x64]


def test_bl():
    assert list(ppc.bl(0x80085760).bytes_for(0x80085760 + 0x9C)) == [0x4b, 0xff, 0xff, 0x65]


def test_beq():
    assert list(ppc.beq(0x80038094).bytes_for(0x80038034)) == [0x41, 0x82, 0x00, 0x60]


def test_bne():
    assert list(ppc.bne(0x80038094).bytes_for(0x80038034)) == [0x40, 0x82, 0x00, 0x60]


def test_blr():
    assert list(ppc.blr().bytes_for(0)) == [0x4e, 0x80, 0x00, 0x20]


def test_bctrl():
    assert list(ppc.bctrl().bytes_for(0)) == [0x4E, 0x80, 0x04, 0x21]


def test_li():
    assert list(ppc.li(ppc.r5, 9999).bytes_for(0)) == [56, 160, 39, 15]


def test_stwu():
    assert list(ppc.stwu(ppc.r1, -0x2C, ppc.r1).bytes_for(0)) == [0x94, 0x21, 0xff, 0xd4]


def test_stmw():
    assert list(ppc.stmw(ppc.r25, -0x2C, ppc.r1).bytes_for(0)) == [191, 33, 255, 212]


def test_sync():
    assert list(ppc.sync().bytes_for(0)) == [0x7c, 0x00, 0x04, 0xac]


def test_isync():
    assert list(ppc.isync().bytes_for(0)) == [0x4c, 0x00, 0x01, 0x2c]


def test_dcbi():
    assert list(ppc.dcbi(1, 2).bytes_for(0)) == [0x7c, 0x01, 0x13, 0xac]


def test_mfspr_LR():
    assert list(ppc.mfspr(ppc.r0, ppc.LR).bytes_for(0)) == [0x7c, 0x08, 0x02, 0xa6]


def test_mtctr():
    assert list(ppc.mtctr(ppc.r12).bytes_for(0)) == [0x7d, 0x89, 0x03, 0xa6]
