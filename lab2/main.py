from collections import defaultdict, deque

class DFA:
    def __init__(self, states, alphabet, transitions, start_state, final_states):
        self.states = states
        self.alphabet = alphabet
        self.transitions = transitions
        self.start_state = start_state
        self.final_states = final_states

    def is_deterministic(self):
        for state in self.states:
            for symbol in self.alphabet:
                next_states = self.transitions.get((state, symbol), set())
                if len(next_states) != 1:
                    return False
        return True

    def minimize(self):
        # Шаг 1: Удаление недостижимых состояний
        reachable_states = self._find_reachable_states()
        states = reachable_states
        final_states = self.final_states & reachable_states

        # Шаг 2: Построение классов эквивалентности
        # Начальное разбиение: конечные и неконечные состояния
        partitions = [final_states, states - final_states]
        if not final_states:
            partitions = [states]
        if not states - final_states:
            partitions = [states]

        changed = True
        while changed:
            changed = False
            new_partitions = []
            for partition in partitions:
                if len(partition) == 1:
                    new_partitions.append(partition)
                    continue
                groups = self._split_partition(partition, partitions)
                if len(groups) > 1:
                    changed = True
                new_partitions.extend(groups)
            partitions = new_partitions

        # Шаг 3: Построение нового автомата
        new_states = set()
        new_transitions = {}
        state_to_partition = {}
        for i, partition in enumerate(partitions):
            new_state = f"q{i}"
            new_states.add(new_state)
            for state in partition:
                state_to_partition[state] = new_state

        for (state, symbol), next_state in self.transitions.items():
            if state in state_to_partition and next_state in state_to_partition:
                new_state_from = state_to_partition[state]
                new_state_to = state_to_partition[next_state]
                new_transitions[(new_state_from, symbol)] = new_state_to

        new_start_state = state_to_partition[self.start_state]
        new_final_states = {state_to_partition[state] for state in final_states}

        return DFA(new_states, self.alphabet, new_transitions, new_start_state, new_final_states)

    def _find_reachable_states(self):
        reachable = {self.start_state}
        queue = deque([self.start_state])
        while queue:
            current = queue.popleft()
            for symbol in self.alphabet:
                next_state = self.transitions.get((current, symbol))
                if next_state and next_state not in reachable:
                    reachable.add(next_state)
                    queue.append(next_state)
        return reachable

    def _split_partition(self, partition, partitions):
        groups = defaultdict(list)
        for state in partition:
            signature = tuple(
                self._find_partition_index(next_state, partitions)
                for symbol in self.alphabet
                for next_state in [self.transitions.get((state, symbol))]
            )
            groups[signature].append(state)
        return list(groups.values())

    def _find_partition_index(self, state, partitions):
        for i, partition in enumerate(partitions):
            if state in partition:
                return i
        return -1

# Пример использования
if __name__ == "__main__":
    # Пример ДКА
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

    if dfa.is_deterministic():
        print("Автомат детерминированный.")
        minimized_dfa = dfa.minimize()
        print("Минимизированный автомат:")
        print("Состояния:", minimized_dfa.states)
        print("Алфавит:", minimized_dfa.alphabet)
        print("Переходы:", minimized_dfa.transitions)
        print("Начальное состояние:", minimized_dfa.start_state)
        print("Конечные состояния:", minimized_dfa.final_states)
    else:
        print("Автомат недетерминированный. Минимизация невозможна.")
