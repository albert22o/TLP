import sys

sys.setrecursionlimit(2000)

class DeterminismError(Exception):
    """Специальный класс ошибки для недетерминированных грамматик."""
    pass

class Parser:
    def __init__(self, grammar, start_terminal):
        self.grammar = grammar
        self.start_terminal = start_terminal
        self.terminals = set()
        self.non_terminals = set(grammar.keys())
        
        for rules in grammar.values():
            for rule in rules:
                for symbol in rule:
                    if symbol not in self.non_terminals and symbol != '':
                        self.terminals.add(symbol)
        print(f"Нетерминалы: {self.non_terminals}")
        print(f"Терминалы: {self.terminals}")

        try:
            self._check_for_determinism_conflicts()
        except DeterminismError as e:
            print(f"ОШИБКА: {e}")
            raise 
        
        self.input_string = ""
        self.max_consumed = -1
        self.failure_reason = ""

    def _check_for_determinism_conflicts(self):
        for non_terminal, rules in self.grammar.items():
            first_terminals_seen = set()
            
            for rule in rules:
                if not rule or rule == ['']:
                    continue
                
                first_sym = rule[0]

                if first_sym in self.terminals:
                    if first_sym in first_terminals_seen:
                        raise DeterminismError(
                            f"Нетерминал '{non_terminal}' имеет несколько правил, "
                            f"начинающихся с одного и того же терминала: '{first_sym}'. "
                        )
                    first_terminals_seen.add(first_sym)

    def _update_failure_reason(self, consumed, reason):
        if consumed > self.max_consumed:
            self.max_consumed = consumed
            self.failure_reason = reason

    def _check(self, string_index, stack):
        if string_index == len(self.input_string) and not stack:
            return True

        if string_index < len(self.input_string) and not stack:
            reason = f"Стек пуст, но в строке остался символ '{self.input_string[string_index]}'."
            self._update_failure_reason(string_index, reason)
            return False

        top = stack.pop(0) 
        
        if top in self.non_terminals:
            for rule in self.grammar[top]:
                new_stack = [s for s in rule if s != ''] + stack
                if self._check(string_index, new_stack):
                    return True
            
            if string_index == len(self.input_string):
                reason = f"Строка закончилась, но нетерминал '{top}' в стеке " \
                         f"не смог успешно раскрыться в эпсилон."
                self._update_failure_reason(string_index, reason)
            
            return False
            
        elif top in self.terminals:
            if string_index == len(self.input_string):
                reason = f"Строка закончилась, но в стеке остался терминал '{top}'."
                self._update_failure_reason(string_index, reason)
                return False
                
            if top != self.input_string[string_index]:
                reason = f"Ошибка на позиции {string_index}: " \
                         f"Ожидался терминал '{top}' (из стека), " \
                         f"но получен символ '{self.input_string[string_index]}'."
                self._update_failure_reason(string_index, reason)
                return False

            return self._check(string_index + 1, stack)
                
        return False


    def parse(self, input_string):
        self.input_string = input_string
        self.max_consumed = -1
        self.failure_reason = "Не найдено ни одного пути разбора."
        initial_stack = [self.start_terminal]
        
        is_accepted = self._check(0, initial_stack)
        
        print(f"Строка: '{input_string}'")
        if is_accepted:
            print("Результат: Принадлежит языку.")
        else:
            print("Результат: Не принадлежит языку.")
            print(f"Причина: {self.failure_reason}")
        return is_accepted