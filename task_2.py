import random
import time
import mmh3
import math
import json

from tabulate import tabulate


class HyperLogLog:
    def __init__(self, p=5):
        self.p = p
        self.m = 1 << p
        self.registers = [0] * self.m
        self.alpha = self._get_alpha()
        self.small_range_correction = 5 * self.m / 2  # Поріг для малих значень

    def _get_alpha(self):
        if self.p <= 16:
            return 0.673
        elif self.p == 32:
            return 0.697
        else:
            return 0.7213 / (1 + 1.079 / self.m)

    def add(self, item):
        if not item:
            raise TypeError(f"Item is empty")
        x = mmh3.hash(str(item["remote_addr"]), signed=False)
        j = x & (self.m - 1)
        w = x >> self.p
        self.registers[j] = max(self.registers[j], self._rho(w))

    def _rho(self, w):
        return len(bin(w)) - 2 if w > 0 else 32

    def count(self):
        Z = sum(2.0 ** -r for r in self.registers)
        E = self.alpha * self.m * self.m / Z

        if E <= self.small_range_correction:
            V = self.registers.count(0)
            if V > 0:
                return self.m * math.log(self.m / V)

        return E

def precise_cardinality(data: list) -> float:
    if not data:
        raise TypeError(f"Data is empty")
    data_set = set()
    for item in data:
        data_set.add(item["remote_addr"])

    return len(data_set)


if __name__ == "__main__":
    # Приклад використання
    hll = HyperLogLog(p=14)
    data = []
    with open("lms-stage-access.log", 'r') as file:
        for line in file.readlines():
            data.append(json.loads(line))
    # Додаємо елементи
    for i in range(100000):
        hll.add(random.choice(data))

    # Оцінюємо наближену кардинальність
    start = time.time()
    estimated_cardinality = hll.count()
    end = time.time()
    hll_time = end - start

    # Оцінюємо точну кардинальність
    start = time.time()
    precise_cardinality = precise_cardinality(data)
    end = time.time()
    set_time = end - start

    print("Результати порівняння:")
    print(tabulate([['Унікальні елементи:', round(precise_cardinality, 2), round(estimated_cardinality, 2)],
                    ['Час виконання (сек.):', round(set_time, 5), round(hll_time, 5)]],
                   headers=['','Точний підрахунок', 'HyperLogLog']))