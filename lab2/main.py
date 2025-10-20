from collections import defaultdict, deque
from typing import Set, Dict, Tuple, FrozenSet

class DFA:
    """
    Универсальный класс для работы с автоматом (поддерживает НКА и ДКА).
    - transitions хранится как (state, symbol) -> set(states)
    - поддерживаются ε-переходы (символом '' - пустая строка)
    - метод minimize() выводит пошаговые разбиения R(0), R(1), ...
    """

    def __init__(self, states: Set[str], alphabet: Set[str],
                 transitions: Dict[Tuple[str, str], object],  # object: str or set
                 start_state: str, final_states: Set[str]):
        # Нормализуем представление переходов: (state, symbol) -> set(states)
        self.states: Set[str] = set(states)
        self.alphabet: Set[str] = set(alphabet)
        self.transitions: Dict[Tuple[str, str], Set[str]] = {}
        for (s, a), tgt in transitions.items():
            if tgt is None:
                continue
            if isinstance(tgt, (set, frozenset, list, tuple)):
                self.transitions[(s, a)] = set(tgt)
            else:
                self.transitions[(s, a)] = {tgt}
        self.start_state = start_state
        self.final_states = set(final_states)

    # ------------------ вспомогательные методы ------------------

    def _has_epsilon(self) -> bool:
        """Проверка наличия ε-переходов (пустая строка '')."""
        for (s, a) in self.transitions:
            if a == '':
                return True
        return False

    def is_deterministic(self) -> bool:
        """
        Проверяет, детерминирован ли автомат:
        - отсутствие ε-переходов
        - для каждой пары (state, symbol) не более одного целевого состояния
        """
        if self._has_epsilon():
            return False
        for (s, a), targets in self.transitions.items():
            if len(targets) > 1:
                return False
        return True

    # ------------------ NFA -> DFA (subset construction) ------------------

    def _epsilon_closure(self, states: Set[str]) -> Set[str]:
        """Возврат ε-замыкания множества состояний."""
        stack = list(states)
        closure = set(states)
        while stack:
            v = stack.pop()
            for tgt in self.transitions.get((v, ''), set()):
                if tgt not in closure:
                    closure.add(tgt)
                    stack.append(tgt)
        return closure

    def nfa_to_dfa(self):
        """
        Преобразует (возможно недетерминированный) автомат в эквивалентный ДКА.
        Имена состояний результата: строка вида "{q0,q1}".
        """
        start_closure = frozenset(sorted(self._epsilon_closure({self.start_state})))
        queue = deque([start_closure])
        seen = {start_closure}
        dfa_states: Set[FrozenSet[str]] = set()
        dfa_trans: Dict[Tuple[str, str], Set[str]] = {}
        dfa_final_states: Set[str] = set()

        while queue:
            subset = queue.popleft()
            dfa_states.add(subset)
            subset_name = self._name_of_subset(subset)
            if any(s in self.final_states for s in subset):
                dfa_final_states.add(subset_name)
            for a in sorted(self.alphabet):
                if a == '':
                    continue
                move_set = set()
                for s in subset:
                    move_set |= self.transitions.get((s, a), set())
                if not move_set:
                    continue
                dest = frozenset(sorted(self._epsilon_closure(move_set)))
                dest_name = self._name_of_subset(dest)
                dfa_trans[(subset_name, a)] = {dest_name}
                if dest not in seen:
                    seen.add(dest)
                    queue.append(dest)

        names = {self._name_of_subset(s) for s in dfa_states}
        dfa_start = self._name_of_subset(start_closure)
        return DFA(names, set(a for a in self.alphabet if a != ''), dfa_trans, dfa_start, dfa_final_states)

    def _name_of_subset(self, subset: FrozenSet[str]) -> str:
        """Приведение подмножества к строковому имени, например {a,b} -> '{a,b}'."""
        if not subset:
            return '{}'
        return "{" + ",".join(sorted(subset)) + "}"

    # ------------------ достижимость ------------------

    def _reachable_states(self, start=None):
        """Возвращает множество достижимых состояний из start (по упорядоченному алфавиту)."""
        if start is None:
            start = self.start_state
        reachable = set()
        queue = deque([start])
        while queue:
            v = queue.popleft()
            if v in reachable:
                continue
            reachable.add(v)
            for a in sorted(self.alphabet):
                for tgt in self.transitions.get((v, a), set()):
                    if tgt not in reachable:
                        queue.append(tgt)
        return reachable

    # ------------------ минимизация с выводом R(0), R(1), ... ------------------

    def _format_partitions(self, partitions):
        """
        Преобразует список блоков (множества состояний) в читаемую строку,
        где каждый блок выводится как {s1,s2,...}. Блоки сортируются для стабильности вывода.
        """
        def sort_key(block):
            return ",".join(sorted(block))
        blocks = sorted([sorted(block) for block in partitions], key=lambda b: (len(b), ",".join(b)))
        blocks_str = ["{" + ",".join(b) + "}" for b in blocks]
        return "[" + ", ".join(blocks_str) + "]"

    def minimize(self):
        """
        Минимизация автомата.
        Если автомат недетерминированный — сначала детерминизируем (nfa_to_dfa),
        затем выполняем метод уточнения разбиений и печатаем R(0), R(1), ...
        """
        # Если автомат недетерминированный — сначала детерминизируем
        if not self.is_deterministic():
            dfa = self.nfa_to_dfa()
            return dfa.minimize()

        # Приводим переходы к виду det_trans[s][a] = tgt (строка), т.к. автомат детерминирован
        det_trans: Dict[str, Dict[str, str]] = {}
        for s in self.states:
            det_trans[s] = {}
            for a in self.alphabet:
                targets = self.transitions.get((s, a), set())
                if not targets:
                    continue
                tgt = next(iter(targets))
                det_trans[s][a] = tgt

        # Удаляем недостижимые состояния
        reachable = self._reachable_states(self.start_state)
        states = set(reachable)

        # Добавляем sink, если есть пропущенные переходы
        sink = "__SINK__"
        if sink in states:
            sink = "__SINK2__"

        need_sink = False
        for s in list(states):
            for a in self.alphabet:
                if a not in det_trans.get(s, {}):
                    need_sink = True
                    break
            if need_sink:
                break

        if need_sink:
            states.add(sink)
            det_trans[sink] = {a: sink for a in self.alphabet}
        for s in states:
            det_trans.setdefault(s, {})
            for a in self.alphabet:
                if a not in det_trans[s]:
                    det_trans[s][a] = sink

        # Инициализация разбиения: финальные / нефинальные
        finals = {s for s in states if s in self.final_states}
        non_finals = states - finals
        partitions = []
        if finals:
            partitions.append(set(finals))
        if non_finals:
            partitions.append(set(non_finals))

        # Печать начального разбиения R(0)
        print("\nПошаговые разбиения:")
        print("R(0) =", self._format_partitions(partitions))

        # Функция получения сигнатуры состояния относительно текущих блоков
        def signature(state, partitions_list):
            sig = []
            for a in sorted(self.alphabet):
                tgt = det_trans[state][a]
                idx = -1
                for i, block in enumerate(partitions_list):
                    if tgt in block:
                        idx = i
                        break
                sig.append(idx)
            return tuple(sig)

        # Итеративное уточнение разбиения с печатью каждого шага
        changed = True
        iter_idx = 1
        while changed:
            changed = False
            new_partitions = []
            for block in partitions:
                buckets = defaultdict(set)
                for s in block:
                    sig = signature(s, partitions)
                    buckets[sig].add(s)
                if len(buckets) > 1:
                    changed = True
                for sub in buckets.values():
                    new_partitions.append(set(sub))
            # Печатаем текущее разбиение R(iter_idx)
            print(f"R({iter_idx}) =", self._format_partitions(new_partitions))
            iter_idx += 1
            partitions = new_partitions

        # Построение минимального автомата по блокам partitions
        block_repr = {}
        for i, block in enumerate(partitions):
            for s in block:
                block_repr[s] = i

        new_states = {f"Q{i}" for i in range(len(partitions))}
        new_start = f"Q{block_repr[self.start_state]}"
        new_finals = {f"Q{block_repr[s]}" for s in states if s in self.final_states}

        new_trans = {}
        for i, block in enumerate(partitions):
            rep = next(iter(block))
            for a in sorted(self.alphabet):
                tgt = det_trans[rep][a]
                j = block_repr[tgt]
                new_trans[(f"Q{i}", a)] = {f"Q{j}"}

        return DFA(new_states, set(self.alphabet), new_trans, new_start, new_finals)

    # ------------------ вывод ------------------
    def pretty_print(self):
        print("Состояния:", self.states)
        print("Алфавит:", self.alphabet)
        print("Начальное состояние:", self.start_state)
        print("Конечные состояния:", self.final_states)
        print("Переходы:")
        for (s, a), tg in sorted(self.transitions.items()):
            print(f"  δ({s}, '{a}') -> {tg}")

# ------------------ пример использования ------------------

if __name__ == "__main__":
    # Пример 1: исходный ДКА из вашего сообщения
    states = {'q0', 'q1', 'q2', 'q3', 'q4', 'q5'}
    alphabet = {'0', '1'}
    transitions = {
        ('q0', '0'): 'q1',
        ('q0', '1'): 'q2',
        ('q1', '0'): 'q0',
        ('q1', '1'): 'q3',
        ('q2', '0'): 'q4',
        ('q2', '1'): 'q5',
        ('q3', '0'): 'q4',
        ('q3', '1'): 'q5',
        ('q4', '0'): 'q4',
        ('q4', '1'): 'q5',
        ('q5', '0'): 'q4',
        ('q5', '1'): 'q5',
    }
    start_state = 'q0'
    final_states = {'q3', 'q4', 'q5'}

    dfa = DFA(states, alphabet, transitions, start_state, final_states)
    print("=== Исходный автомат (пример 1) ===")
    dfa.pretty_print()
    minimized = dfa.minimize()
    print("\n=== Минимизированный автомат ===")
    minimized.pretty_print()

    # Пример 2: НКА (множественные цели)
    nfa_states = {'p', 'q', 'r'}
    nfa_alphabet = {'0', '1'}
    nfa_transitions = {
        ('p', '0'): {'p'},
        ('p', '1'): {'p', 'q'},
        ('q', '1'): {'r'},
        # r без переходов
    }
    nfa_start = 'p'
    nfa_finals = {'r'}

    nfa = DFA(nfa_states, nfa_alphabet, nfa_transitions, nfa_start, nfa_finals)
    print("\n\n=== Исходный НКА (пример 2) ===")
    nfa.pretty_print()
    minimized_from_nfa = nfa.minimize()
    print("\n=== Результат: НКА -> ДКА -> Минимизация ===")
    minimized_from_nfa.pretty_print()
