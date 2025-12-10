class DPDATransducer:
    def __init__(self, transitions, start_state, final_states, start_stack_symbol):
        self.transitions = transitions
        self.start_state = start_state
        self.final_states = final_states
        self.start_stack_symbol = start_stack_symbol

    def translate(self, input_string):
        stack = [self.start_stack_symbol]
        current_state = self.start_state
        cursor = 0
        output_tape = []

        step = 0
        while True:
            current_char = input_string[cursor] if cursor < len(input_string) else None

            if not stack:
                return None, "Ошибка: Стек опустел до завершения обработки."

            stack_top = stack[-1]

            key = (current_state, current_char, stack_top)
            epsilon_key = (current_state, None, stack_top)

            transition = None
            consumed_input = False

            if current_char is not None and key in self.transitions:
                transition = self.transitions[key]
                consumed_input = True
            elif epsilon_key in self.transitions:
                transition = self.transitions[epsilon_key]
                consumed_input = False
            else:
                if current_char is None and current_state in self.final_states:
                    return "".join(output_tape).strip(), "Успех"
                
                if current_char is None:
                    return None, f"Строка кончилась, но состояние '{current_state}' не финальное."
                else:
                    return None, f"Нет перехода: State={current_state}, Input={current_char}, Stack={stack_top}"

            new_state, symbols_to_push, output_symbol = transition

            if output_symbol:
                output_tape.append(output_symbol)

            stack.pop()
            if symbols_to_push:
                for symbol in reversed(symbols_to_push):
                    stack.append(symbol)

            current_state = new_state

            if consumed_input:
                cursor += 1

            step += 1
            if step > 1000:
                return None, "Ошибка: Бесконечный цикл (переполнение шагов)."


if __name__ == "__main__":
    start_state = 'q0'
    final_states = {'qf'}
    start_stack_symbol = 'Z' 

    transitions = {
        ('q0', '5', 'Z'): ('q0', 'Z', '5 '), 
        ('q0', '3', '+'): ('q0', '+', '3 '),
        ('q0', '2', '*'): ('q0', '*', '2 '),

        ('q0', '+', 'Z'): ('q0', '+Z', ''), 

        ('q0', '*', '+'): ('q0', '*+', ''),

        ('q0', None, '*'): ('q0', '', '* '),
        ('q0', None, '+'): ('q0', '', '+ '),
        ('q0', None, 'Z'): ('qf', 'Z', ''),
    }

    dpda = DPDATransducer(transitions, start_state, final_states, start_stack_symbol)

    expression = "5+3*2" 

    print(f"Входное выражение: {expression}")
    result_opz, status = dpda.translate(expression)
    
    print("-" * 40)
    if result_opz is not None:
        print(f"Результат (ОПЗ): {result_opz}")
        print(f"Статус: {status}")
    else:
        print(f"Ошибка: {status}")