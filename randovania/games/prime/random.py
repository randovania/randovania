# consts
MBIG = 0x7fffffff
MSEED = 0x9a4ec86
MZ = 0


class Random:
    def __init__(self, seed):
        self.SeedArray = [0] * 56

        # Initialize our Seed array.
        # This algorithm comes from Numerical Recipes in C (2nd Ed.)
        if seed == -2147483648:
            subtraction = 0x7fffffff
        else:
            subtraction = abs(seed)
        mj = MSEED - subtraction
        self.SeedArray[55] = mj
        mk = 1
        # Apparently the range [1..55] is special (Knuth) and so we're wasting the 0'th position.
        for i in range(1, 55):
            ii = (21 * i) % 55
            self.SeedArray[ii] = mk
            mk = mj - mk
            if mk < 0:
                mk += MBIG
            mj = self.SeedArray[ii]
        for k in range(1, 5):
            for i in range(1, 56):
                self.SeedArray[i] -= self.SeedArray[1 + (i + 30) % 55]
                if self.SeedArray[i] < 0:
                    self.SeedArray[i] += MBIG

        self.inext = 0
        self.inextp = 21

    def next_with_max(self, max_value):
        return int(self.sample() * max_value)

    def next_with_min_max(self, min_value, max_value):
        num = max_value - min_value
        if num <= 0x7fffffff:
            return int(self.sample() * num) + min_value
        return int(self.get_sample_for_large_range() * num) + min_value

    def get_sample_for_large_range(self):
        num = self._internal_sample()
        if self._internal_sample() % 2 == 0:
            num = -num
        return (num + 2147483646.0) / 4294967293

    def _internal_sample(self):
        inext = self.inext
        inextp = self.inextp

        inext += 1
        if inext >= 0x38:
            inext = 1

        inextp += 1
        if inextp >= 0x38:
            inextp = 1

        num = self.SeedArray[inext] - self.SeedArray[inextp]
        if num == 0x7fffffff:
            num -= 1
        if num < 0:
            num += 0x7fffffff

        self.SeedArray[inext] = num
        self.inext = inext
        self.inextp = inextp
        return num

    def sample(self):
        return self._internal_sample() * 4.6566128752457969E-10
