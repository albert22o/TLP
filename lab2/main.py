from collections import defaultdict, deque
from typing import Set, Dict, Tuple, FrozenSet

class DFA:
    def __init__(self, states: Set[str], alphabet: Set[str],
                 transitions: Dict[Tuple[str, str], object], 
                 start_state: str, final_states: Set[str]):
        self.states: Set[str] = set(states)
        self.alphabet: Set[str] = set(alphabet)
        self.transitions: Dict[Tuple[str, str], Set[str]] = {}
        for (s, a), tgt in transitions.items():
            if tgt is None:
                continue
            # По условию эпсилон-переходов нет, 'a' не может быть ''
            if isinstance(tgt, (set, frozenset, list, tuple)):
                self.transitions[(s, a)] = set(tgt)
            else:
                self.transitions[(s, a)] = {tgt}
        self.start_state = start_state
        self.final_states = set(final_states)

    def is_deterministic(self) -> bool:
        for (s, a), targets in self.transitions.items():
            if len(targets) > 1:
                return False
        return True

    def nfa_to_dfa(self):
        start_subset = frozenset({self.start_state})
        queue = deque([start_subset])
        seen = {start_subset}
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
                move_set = set()
                for s in subset:
                    move_set |= self.transitions.get((s, a), set())
                if not move_set:
                    continue
                dest = frozenset(sorted(move_set))
                dest_name = self._name_of_subset(dest)
                dfa_trans[(subset_name, a)] = {dest_name}
                
                if dest not in seen:
                    seen.add(dest)
                    queue.append(dest)

        names = {self._name_of_subset(s) for s in dfa_states}
        dfa_start = self._name_of_subset(start_subset)
        return DFA(names, self.alphabet, dfa_trans, dfa_start, dfa_final_states)

    def _name_of_subset(self, subset: FrozenSet[str]) -> str:
        if not subset:
            return '{}' 
        return "{" + ",".join(sorted(subset)) + "}"

    def _reachable_states(self, start=None):
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

    def _format_partitions(self, partitions):
        def sort_key(block):
            return ",".join(sorted(block))
        blocks = sorted([sorted(block) for block in partitions], key=lambda b: (len(b), ",".join(b)))
        blocks_str = ["{" + ",".join(b) + "}" for b in blocks]
        return "[" + ", ".join(blocks_str) + "]"

    def minimize(self):
        if not self.is_deterministic():
            print("Автомат не детерминированный. Выполняется детерминизация...")
            dfa = self.nfa_to_dfa()
            print("=== Результат детерминизации ===")
            dfa.pretty_print()
            return dfa.minimize()
        det_trans: Dict[str, Dict[str, str]] = {}
        for s in self.states:
            det_trans[s] = {}
            for a in self.alphabet:
                targets = self.transitions.get((s, a), set())
                if not targets:
                    continue
                if targets:
                    tgt = next(iter(targets))
                    det_trans[s][a] = tgt
        reachable = self._reachable_states(self.start_state)
        states = set(reachable)
        unreachable = self.states - reachable
        if unreachable:
            print(f"Удалены недостижимые состояния: {sorted(unreachable)}")
        
        if not states:
             print("\nАвтомат пуст (нет достижимых состояний). Минимизация не требуется.")
             return self 

        finals = {s for s in states if s in self.final_states}
        non_finals = states - finals
        partitions = []
        if finals:
            partitions.append(set(finals))
        if non_finals:
            partitions.append(set(non_finals))

        if len(partitions) == 1:
            print("\nПошаговые разбиения:")
            print("R(0) =", self._format_partitions(partitions))
            print("Все достижимые состояния эквивалентны (все финальные или все нефинальные).")

        print("\nПошаговые разбиения:")
        print("R(0) =", self._format_partitions(partitions))

        def signature(state, partitions_list):
            sig = []
            for a in sorted(self.alphabet):
                tgt = det_trans[state].get(a)
                idx = -1
                for i, block in enumerate(partitions_list):
                    if tgt in block:
                        idx = i
                        break
                sig.append(idx)
            return tuple(sig)

        changed = True
        iter_idx = 1
        while changed:
            changed = False
            new_partitions = []
            for block in partitions:
                if len(block) <= 1:
                    new_partitions.append(block)
                    continue
                    
                buckets = defaultdict(set)
                for s in block:
                    sig = signature(s, partitions)
                    buckets[sig].add(s)
                
                if len(buckets) > 1:
                    changed = True
                
                for sub in buckets.values():
                    new_partitions.append(set(sub))
            
            if not changed:
                 print(f"R({iter_idx}) = R({iter_idx-1}). Разбиение стабилизировалось.")
                 break
                 
            print(f"R({iter_idx}) =", self._format_partitions(new_partitions))
            iter_idx += 1
            partitions = new_partitions
        
        block_map: Dict[str, str] = {}
        block_names: Dict[FrozenSet[str], str] = {}
        
        sorted_partitions = sorted([frozenset(b) for b in partitions], key=lambda b: ",".join(sorted(b)))
        
        for i, block in enumerate(sorted_partitions):
            block_name = f"Q{i}"
            block_names[block] = block_name
            for s in block:
                block_map[s] = block_name
        
        new_states = set(block_names.values())
        
        if self.start_state not in block_map:
             print("Ошибка: Исходное начальное состояние недостижимо.")
             return DFA(set(), self.alphabet, {}, "", set())

        new_start = block_map[self.start_state]
        new_finals = {block_map[s] for s in states if s in self.final_states}

        new_trans = {}
        for block in sorted_partitions:
            rep = next(iter(block))
            block_name = block_map[rep]
            
            for a in sorted(self.alphabet):
                tgt = det_trans[rep][a]
                tgt_block_name = block_map[tgt]
                new_trans[(block_name, a)] = {tgt_block_name}

        return DFA(new_states, self.alphabet, new_trans, new_start, new_finals)

    def pretty_print(self):
        if not self.states:
            print("Автомат пуст.")
            print("Алфавит:", self.alphabet)
            return
            
        print("Состояния:", sorted(self.states))
        print("Алфавит:", sorted(self.alphabet))
        print("Начальное состояние:", self.start_state)
        print("Конечные состояния:", sorted(self.final_states))
        print("Переходы:")
        sorted_trans = sorted(self.transitions.items(), key=lambda item: (item[0][0], item[0][1]))
        for (s, a), tg in sorted_trans:
            if self.is_deterministic():
                 tgt_str = next(iter(tg)) if tg else "{}"
                 print(f"  δ({s}, '{a}') -> {tgt_str}")
            else:
                 print(f"  δ({s}, '{a}') -> {sorted(tg)}")


if __name__ == "__main__":
    states = {'q0', 'q1', 'q2', 'q3', 'q4'}
    alphabet = {'0', '1'}
    transitions = {
        ('q0', '0'): {'q0','q1'},
        ('q0', '1'): 'q0',
        ('q1', '0'): 'q2',
        ('q1', '1'): 'q2',
        ('q2', '0'): 'q3',
        ('q2', '1'): 'q3',
        ('q3', '0'): 'q4',
        ('q3', '1'): 'q4',
    }
    start_state = 'q0'
    final_states = {'q4'}

    dfa = DFA(states, alphabet, transitions, start_state, final_states)
    print("=== Исходный автомат (пример 1) ===")
    dfa.pretty_print()
    minimized = dfa.minimize()
    print("\n=== Минимизированный автомат ===")
    minimized.pretty_print()

    nfa_states = {'p', 'q', 'r'}
    nfa_alphabet = {'0', '1'}
    nfa_transitions = {
        ('p', '0'): {'p'},
        ('p', '1'): {'p', 'q'},
        ('q', '1'): {'r'},
    }
    nfa_start = 'p'
    nfa_finals = {'r'}

    nfa = DFA(nfa_states, nfa_alphabet, nfa_transitions, nfa_start, nfa_finals)
    print("\n\n=== Исходный НКА (пример 2) ===")
    nfa.pretty_print()
    minimized_from_nfa = nfa.minimize()
    print("\n=== Результат: НКА -> ДКА -> Минимизация ===")
    minimized_from_nfa.pretty_print()