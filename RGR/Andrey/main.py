import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import random

# --- 1. Классы автоматов (Без изменений) ---
class State:
    _id_counter = 0

    def __init__(self, is_final=False):
        self.id = State._id_counter
        State._id_counter += 1
        self.is_final = is_final
        self.transitions = {}  # char -> list of States
        self.epsilon_transitions = []

    def add_transition(self, char, state):
        if char not in self.transitions:
            self.transitions[char] = []
        self.transitions[char].append(state)

    def add_epsilon(self, state):
        self.epsilon_transitions.append(state)

    def __repr__(self):
        return f"S{self.id}"

class NFA:
    def __init__(self, start, end):
        self.start = start
        self.end = end 

class DFA:
    def __init__(self):
        self.start_state = None
        self.final_states = set()
        self.transitions = {} # (state_id, char) -> next_state_id

# --- 2. Логика алгоритмов ---

def preprocess_regex(regex):
    """Добавляет явный символ конкатенации '.'"""
    output = []
    valid_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
    
    for i in range(len(regex)):
        c1 = regex[i]
        output.append(c1)
        if i + 1 < len(regex):
            c2 = regex[i+1]
            # Логика вставки точки: 
            # Между символом/закрывающей скобкой/звездочкой И символом/открывающей скобкой
            is_c1_operand = (c1 in valid_chars or c1 == '*' or c1 == ')')
            is_c2_operand = (c2 in valid_chars or c2 == '(')
            
            if is_c1_operand and is_c2_operand:
                output.append('.')
    return "".join(output)

def regex_to_postfix(regex, log_func=print):
    """Алгоритм сортировочной станции"""
    preprocessed = preprocess_regex(regex)
    log_func(f"1. Предобработка: {regex} -> {preprocessed}")
    
    postfix = ""
    stack = []
    precedence = {'*': 3, '.': 2, '|': 1, '(': 0}

    for char in preprocessed:
        if char.isalnum():
            postfix += char
        elif char == '(':
            stack.append(char)
        elif char == ')':
            while stack and stack[-1] != '(':
                postfix += stack.pop()
            if stack: stack.pop()
        else:
            while stack and precedence.get(stack[-1], 0) >= precedence.get(char, 0):
                postfix += stack.pop()
            stack.append(char)

    while stack:
        postfix += stack.pop()
    
    log_func(f"   Постфиксная запись: {postfix}\n")
    return postfix

def build_nfa(postfix, log_func=print):
    stack = []
    log_func("2. Построение НКА (Алгоритм Томпсона):")
    
    # Сброс счетчика состояний перед построением происходит в GUI классе,
    # но здесь мы просто строим
    
    for char in postfix:
        if char == '.':
            nfa2 = stack.pop()
            nfa1 = stack.pop()
            nfa1.end.is_final = False
            nfa1.end.add_epsilon(nfa2.start)
            new_nfa = NFA(nfa1.start, nfa2.end)
            stack.append(new_nfa)
            log_func(f"   [.] Конкатенация")
            
        elif char == '|':
            nfa2 = stack.pop()
            nfa1 = stack.pop()
            start = State()
            end = State(is_final=True)
            start.add_epsilon(nfa1.start)
            start.add_epsilon(nfa2.start)
            nfa1.end.is_final = False
            nfa2.end.is_final = False
            nfa1.end.add_epsilon(end)
            nfa2.end.add_epsilon(end)
            new_nfa = NFA(start, end)
            stack.append(new_nfa)
            log_func(f"   [|] Объединение")

        elif char == '*':
            nfa = stack.pop()
            start = State()
            end = State(is_final=True)
            start.add_epsilon(nfa.start)
            start.add_epsilon(end)
            nfa.end.is_final = False
            nfa.end.add_epsilon(nfa.start)
            nfa.end.add_epsilon(end)
            new_nfa = NFA(start, end)
            stack.append(new_nfa)
            log_func(f"   [*] Замыкание Клини")
            
        else:
            start = State()
            end = State(is_final=True)
            start.add_transition(char, end)
            new_nfa = NFA(start, end)
            stack.append(new_nfa)
            log_func(f"   [sym] Символ '{char}': S{start.id} -> S{end.id}")

    if not stack:
        raise ValueError("Пустой стек после построения НКА (ошибка выражения)")
    return stack.pop()

def get_epsilon_closure(states):
    stack = list(states)
    closure = set(states)
    while stack:
        s = stack.pop()
        for next_s in s.epsilon_transitions:
            if next_s not in closure:
                closure.add(next_s)
                stack.append(next_s)
    return frozenset(sorted(closure, key=lambda x: x.id))

def get_move(states, char):
    result = set()
    for s in states:
        if char in s.transitions:
            for next_s in s.transitions[char]:
                result.add(next_s)
    return result

def nfa_to_dfa(nfa, alphabet, log_func=print):
    log_func("\n3. Преобразование НКА в ДКА (Метод подмножеств):")
    start_closure = get_epsilon_closure({nfa.start})
    dfa_states = {start_closure: 0}
    queue = [start_closure]
    
    dfa = DFA()
    dfa.start_state = 0
    
    processed_count = 0
    while processed_count < len(queue):
        current_set = queue[processed_count]
        current_dfa_id = dfa_states[current_set]
        processed_count += 1
        
        # Если хотя бы одно состояние НКА в множестве финальное, то и состояние ДКА финальное
        for s in current_set:
            if s.is_final:
                dfa.final_states.add(current_dfa_id)
                break
        
        ids_in_set = [s.id for s in current_set]
        # log_func(f"   Обработка D{current_dfa_id} {ids_in_set}")

        for char in alphabet:
            move_res = get_move(current_set, char)
            epsilon_res = get_epsilon_closure(move_res)
            
            if not epsilon_res:
                continue
                
            if epsilon_res not in dfa_states:
                new_id = len(dfa_states)
                dfa_states[epsilon_res] = new_id
                queue.append(epsilon_res)
            
            target_id = dfa_states[epsilon_res]
            dfa.transitions[(current_dfa_id, char)] = target_id
            log_func(f"   D{current_dfa_id} --({char})--> D{target_id} (Множество НКА: {[s.id for s in epsilon_res]})")
            
    return dfa

def simulate_nfa(nfa, string):
    current_states = get_epsilon_closure({nfa.start})
    for char in string:
        move_result = get_move(current_states, char)
        current_states = get_epsilon_closure(move_result)
        if not current_states: return False
    for s in current_states:
        if s.is_final: return True
    return False

def simulate_dfa(dfa, string):
    current = dfa.start_state
    for char in string:
        if (current, char) in dfa.transitions:
            current = dfa.transitions[(current, char)]
        else:
            return False
    return current in dfa.final_states

# --- 3. Графический интерфейс ---

class RegexApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Курсовая работа: Regex -> NFA -> DFA")
        self.root.geometry("800x700")
        
        self.nfa = None
        self.dfa = None
        self.alphabet = []
        
        self._create_menu()
        self._setup_ui()

    def _create_menu(self):
        menubar = tk.Menu(self.root)
        
        # Меню "Файл"
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Сохранить результаты...", command=self.save_to_file)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.root.quit)
        menubar.add_cascade(label="Файл", menu=file_menu)
        
        # Меню "Инфо"
        info_menu = tk.Menu(menubar, tearoff=0)
        info_menu.add_command(label="Автор", command=self.show_author)
        info_menu.add_command(label="Тема", command=self.show_topic)
        menubar.add_cascade(label="Инфо", menu=info_menu)

        # Меню "Помощь"
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Формат данных", command=self.show_help)
        menubar.add_cascade(label="Помощь", menu=help_menu)

        self.root.config(menu=menubar)

    def _setup_ui(self):
        # Панель ввода
        input_frame = ttk.LabelFrame(self.root, text="Входные данные", padding=10)
        input_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(input_frame, text="Регулярное выражение:").pack(side="left")
        self.regex_entry = ttk.Entry(input_frame, width=35, font=("Consolas", 12))
        self.regex_entry.pack(side="left", padx=10)
        self.regex_entry.insert(0, "(a|b)*abb")
        
        ttk.Button(input_frame, text="?", width=3, command=self.show_help).pack(side="left", padx=(0, 10))
        
        btn_calc = ttk.Button(input_frame, text="Расчёты (Построить)", command=self.build_automata)
        btn_calc.pack(side="left", padx=5)

        # Панель лога
        log_frame = ttk.LabelFrame(self.root, text="Ход преобразований", padding=10)
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.log_area = scrolledtext.ScrolledText(log_frame, state='disabled', font=("Consolas", 10))
        self.log_area.pack(fill="both", expand=True)

        # Панель тестирования
        test_frame = ttk.LabelFrame(self.root, text="Проверка эквивалентности", padding=10)
        test_frame.pack(fill="x", padx=10, pady=10)
        
        # Ручной ввод
        f1 = ttk.Frame(test_frame)
        f1.pack(fill="x", pady=5)
        ttk.Label(f1, text="Ручной тест строки:").pack(side="left")
        self.test_entry = ttk.Entry(f1, width=20, font=("Consolas", 11))
        self.test_entry.pack(side="left", padx=10)
        ttk.Button(f1, text="Проверить одну", command=self.check_single_string).pack(side="left")
        self.result_label = ttk.Label(f1, text="", font=("Arial", 10, "bold"))
        self.result_label.pack(side="left", padx=10)

        # Автоматический тест
        f2 = ttk.Frame(test_frame)
        f2.pack(fill="x", pady=5)
        ttk.Label(f2, text="Авто-тест (генерация цепочек):").pack(side="left")
        ttk.Button(f2, text="Сгенерировать и проверить 20 строк", command=self.auto_verify).pack(side="left", padx=10)

    # --- Логика GUI ---

    def log(self, message):
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')

    def clear_log(self):
        self.log_area.config(state='normal')
        self.log_area.delete(1.0, tk.END)
        self.log_area.config(state='disabled')

    def show_author(self):
        messagebox.showinfo("Автор", "Студент: Лацук А.Ю.\nГруппа: ИП-211")

    def show_topic(self):
        msg = ("Тема задания: Реализация алгоритма Томпсона и "
               "преобразование НКА в ДКА.\n\n"
               "Программа строит автоматы по регулярному выражению "
               "и проверяет их эквивалентность.")
        messagebox.showinfo("Тема", msg)

    def show_help(self):
        msg = ("Формат входных данных:\n"
               "Поддерживаются латинские буквы и цифры.\n"
               "Операторы:\n"
               "  |  - ИЛИ (объединение)\n"
               "  * - Звездочка Клини (повторение 0 или более раз)\n"
               "  () - Группировка\n"
               "Конкатенация обозначается просто написанием символов подряд (ab).\n\n"
               "Пример: (a|b)*c")
        messagebox.showinfo("Справка", msg)

    def save_to_file(self):
        text_content = self.log_area.get("1.0", tk.END).strip()
        if not text_content:
            messagebox.showwarning("Внимание", "Нет данных для сохранения.")
            return
            
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if filename:
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(text_content)
                messagebox.showinfo("Успех", f"Данные сохранены в {filename}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{e}")

    def build_automata(self):
        regex = self.regex_entry.get().strip()
        if not regex:
            messagebox.showwarning("Ошибка", "Введите регулярное выражение!")
            return

        self.clear_log()
        self.nfa = None
        self.dfa = None
        State._id_counter = 0 # Важно: сброс ID

        try:
            self.log(f"--- НАЧАЛО РАСЧЁТА ДЛЯ: {regex} ---")
            postfix = regex_to_postfix(regex, log_func=self.log)
            self.nfa = build_nfa(postfix, log_func=self.log)
            
            # Извлекаем алфавит из выражения для DKA
            self.alphabet = sorted(list(set(c for c in regex if c.isalnum())))
            self.log(f"Алфавит: {self.alphabet}")
            
            self.dfa = nfa_to_dfa(self.nfa, self.alphabet, log_func=self.log)
            
            self.log(f"\nФинальные состояния ДКА: {self.dfa.final_states}")
            self.log("--- ПОСТРОЕНИЕ ЗАВЕРШЕНО ---\n")
            messagebox.showinfo("Готово", "Автоматы успешно построены!")
            
        except Exception as e:
            self.log(f"\nОШИБКА: {str(e)}")
            messagebox.showerror("Ошибка выполнения", f"Произошла ошибка:\n{e}")

    def check_single_string(self):
        if not self.nfa or not self.dfa:
            messagebox.showwarning("Внимание", "Сначала выполните расчёты!")
            return
        
        s = self.test_entry.get().strip()
        res_nfa = simulate_nfa(self.nfa, s)
        res_dfa = simulate_dfa(self.dfa, s)
        
        color = "green" if res_dfa else "red"
        status = "OK" if res_nfa == res_dfa else "FAIL"
        
        res_text = f"НКА: {res_nfa}, ДКА: {res_dfa}"
        self.result_label.config(text=f"{res_text} [{status}]", foreground=color)
        self.log(f"Тест '{s}': {res_text}")

    def auto_verify(self):
        """Генерация случайных цепочек для проверки эквивалентности"""
        if not self.nfa or not self.dfa:
            messagebox.showwarning("Внимание", "Сначала выполните расчёты!")
            return

        if not self.alphabet:
            self.alphabet = ['a', 'b'] # Дефолтный, если вдруг пустой

        self.log("\n--- ЗАПУСК АВТОМАТИЧЕСКОЙ ПРОВЕРКИ ---")
        errors = 0
        count = 20
        
        # Генерируем строки разной длины
        test_set = [""] # Всегда проверяем пустую строку
        for _ in range(count):
            length = random.randint(1, 8)
            s = "".join(random.choice(self.alphabet) for _ in range(length))
            test_set.append(s)
            
        for s in test_set:
            res_nfa = simulate_nfa(self.nfa, s)
            res_dfa = simulate_dfa(self.dfa, s)
            
            match_icon = "MATCH" if res_nfa == res_dfa else "ERROR"
            if res_nfa != res_dfa:
                errors += 1
                
            self.log(f"Str: '{s:10}' | NFA: {str(res_nfa):5} | DFA: {str(res_dfa):5} -> {match_icon}")

        result_msg = f"Проверено строк: {len(test_set)}. Ошибок: {errors}."
        self.log(f"--- ИТОГ: {result_msg} ---")
        
        if errors == 0:
            messagebox.showinfo("Результат теста", f"Эквивалентность подтверждена!\n{result_msg}")
        else:
            messagebox.showerror("Результат теста", f"Найдены расхождения!\n{result_msg}")

if __name__ == "__main__":
    root = tk.Tk()
    # Применение стиля для улучшения внешнего вида
    style = ttk.Style()
    style.theme_use('clam') 
    
    app = RegexApp(root)
    root.mainloop()