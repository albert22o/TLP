class DPDA:
    def __init__(self, transitions, start_state, final_states, start_stack_symbol):
        self.transitions = transitions
        self.start_state = start_state
        self.final_states = final_states
        self.start_stack_symbol = start_stack_symbol

    def validate(self, input_string):
        stack = [self.start_stack_symbol]
        current_state = self.start_state
        cursor = 0  
        

        step = 0
        while True:
            current_char = input_string[cursor] if cursor < len(input_string) else None

            if not stack:
                return False, "Стек опустел до завершения обработки или перехода в финальное состояние."

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
                    return True, "Цепочка принята (достигнуто финальное состояние)."
                
                if current_char is None:
                    return False, f"Цепочка закончилась, но состояние '{current_state}' не является финальным."
                else:
                    return False, f"Нет перехода из состояния '{current_state}' по символу '{current_char}' с вершиной стека '{stack_top}'."

            new_state, symbols_to_push = transition

            #print(f"Шаг {step}: {current_state}, Вход: '{current_char if consumed_input else 'ε'}', Стек: {stack} -> {new_state}")

            stack.pop() 

            if symbols_to_push:
                for symbol in reversed(symbols_to_push):
                    stack.append(symbol)
            
            current_state = new_state
            
            if consumed_input:
                cursor += 1
            
            step += 1
            
            if step > 1000:
                return False, "Бесконечная рекурсия"



if __name__ == "__main__":
    # Пример языка: L = {0^n 1^n | n >= 1} (равное количество 0 и 1)
    # Логика: 
    # 1. Читаем 0, кладем A в стек.
    # 2. Читаем 1, снимаем A из стека.
    # 3. В конце стек должен остаться только с Z.

    # transitions = {
    #     ('q0', '0', 'Z'): ('q0', '0Z'), # Первый ноль, кладем 0 поверх Z
    #     ('q0', '0', '0'): ('q0', '00'), # Последующие нули, кладем 0 поверх 0
        
    #     # Переход к единицам
    #     ('q0', '1', '0'): ('q1', ''),   # Встретили 1, меняем состояние, снимаем 0
        
    #     # q1: читаем единицы, снимаем 0
    #     ('q1', '1', '0'): ('q1', ''),   # Снимаем 0
        
    #     # Финальный переход
    #     ('q1', None, 'Z'): ('q3', 'Z'), # Переход в допускающее состояние
    #     #('q3', None, 'Z'): ('q1', 'Z')
    # }

    # start_state = 'q0'
    # final_states = {'qf'}
    # start_stack_symbol = 'Z'

    transitions = {
        ('q0', 'a', 'Z'): ('q0', 'aZ'),
        ('q0', 'a', 'a'): ('q1', 'a'),
        ('q1', 'a', 'a'): ('q0', 'aa'),
        ('q7', 'b', 'a'): ('q2', ''),
        ('q2', 'b', 'a'): ('q2', ''),
        ('q2', None, 'a'): ('q3', ''),
        ('q3', None, 'a'): ('q4', ''),
        ('q4', None, 'Z'): ('q8', 'Z'),
        ('q0', 'c', 'a'): ('q5', 'a'),
        ('q5', 'c', 'a'): ('q6', 'a'),
        ('q6', 'c', 'a'): ('q7', 'a'),
        ('q7', 'c', 'a'): ('q7', 'a'),
        ('q7', None, 'a'): ('q20', ''),
        ('q20', None, 'a'): ('q21', ''),
        ('q21', None, 'Z'): ('q4', 'Z'),
        ('q20', None, 'Z'): ('q4', 'Z'),
    }

    start_state = 'q0'
    final_states = {'q8'}
    start_stack_symbol = 'Z'



    dpda = DPDA(transitions, start_state, final_states, start_stack_symbol)

    # Тестовые цепочки
    test_cases = [
        # "01",       # Принята
        # "0011",     # Принята
        # "000111",   # Принята
        # "011",      # Отвергнута (много 1)
        # "001",      # Отвергнута (мало 1)
        # "10",       # Отвергнута (порядок)
        # "00000",    # Отвергнута (нет 1)
        # "001101",   # Отвергнута (порядок)
        "aaaccc",
        "aaaccc",
        "aaacccb",
        "aaaaacccccbb",
        "aaaaacccccb",

    ]

    print(f"{'ЦЕПОЧКА':<10} | {'РЕЗУЛЬТАТ':<10} | {'ПРИЧИНА'}")
    print("-" * 80)

    for text in test_cases:
        result, reason = dpda.validate(text)
        status = "ПРИНЯТА" if result else "ОТКАЗ"
        print(f"{text:<10} | {status:<10} | {reason}")