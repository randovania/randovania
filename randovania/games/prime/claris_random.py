from typing import List


class Int32:
    def __init__(self, value):
        # Wrap value into [-2**31, 2**31-1]
        self.value = (value + 2 ** 31) % 2 ** 32 - 2 ** 31

    def __int__(self):
        return self.value

    def __add__(self, other):
        return Int32(self.value + other.value)

    def __sub__(self, other):
        return Int32(self.value - other.value)


# consts
MBIG = Int32(0x7fffffff)
MSEED = Int32(0x9a4ec86)
MZ = 0


class Random:
    """Reference implementation:
    https://github.com/EthanArmbrust/new-prime-seed-generator/blob/master/src/Random.cpp"""

    def __init__(self, seed):
        self.SeedArray = [Int32(0)] * 56  # type: List[Int32]

        if seed < 0:
            raise ValueError("Invalid seed: must be >= 0")

        if seed > 0x7fffffff:
            raise ValueError("Invalid seed: must be <= 0x7fffffff (2147483647)")

        # Initialize our Seed array.
        # This algorithm comes from Numerical Recipes in C (2nd Ed.)
        mj = MSEED - Int32(seed)
        self.SeedArray[55] = mj
        mk = Int32(1)
        # Apparently the range [1..55] is special (Knuth) and so we're wasting the 0'th position.
        for i in range(1, 55):
            ii = (21 * i) % 55
            self.SeedArray[ii] = mk
            mk = mj - mk
            if mk.value < 0:
                mk += MBIG
            mj = self.SeedArray[ii]

        for _ in range(1, 5):
            for i in range(1, 56):
                idx = 1 + (i + 30) % 55
                self.SeedArray[i] -= self.SeedArray[idx]
                if self.SeedArray[i].value < 0:
                    self.SeedArray[i] += MBIG

        self.inext = 0
        self.inextp = 21

    def next_with_max(self, max_value: int) -> int:
        return int(self.sample() * max_value)

    def _internal_sample(self) -> Int32:
        inext = self.inext
        inextp = self.inextp

        inext += 1
        if inext >= 0x38:
            inext = 1

        inextp += 1
        if inextp >= 0x38:
            inextp = 1

        num = self.SeedArray[inext] - self.SeedArray[inextp]
        if num == MBIG:
            num -= 1
        if num.value < 0:
            num += MBIG

        self.SeedArray[inext] = num
        self.inext = inext
        self.inextp = inextp
        return num

    def sample(self) -> float:
        return self._internal_sample().value / MBIG.value
