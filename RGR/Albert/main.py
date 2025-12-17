import sys
import copy
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog

# ==========================================
# ЧАСТЬ 1: ЛОГИКА (КЛАССЫ CFG, CNF, GENERATOR)
# ==========================================

class CFG:
    """Класс для представления контекстно-свободной грамматики."""
    def __init__(self):
        self.rules = {}
        self.start_symbol = None
        self.terminals = set()
        self.non_terminals = set()

    def parse_from_text(self, text):
        """Парсит текст грамматики. Формат: S -> A B | a"""
        self.rules = {}
        lines = text.strip().split('\n')
        first_symbol = None

        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line: continue
            
            if '->' not in line:
                raise ValueError(f"Строка {line_num}: отсутствует '->'.")
            
            lhs, rhs_part = line.split('->')
            lhs = lhs.strip()
            
            if not lhs.isupper():
                raise ValueError(f"Строка {line_num}: Нетерминал '{lhs}' должен быть заглавным.")

            if first_symbol is None:
                first_symbol = lhs

            if lhs not in self.rules:
                self.rules[lhs] = []

            alternatives = rhs_part.split('|')
            for alt in alternatives:
                # Разбиваем по пробелам, чтобы отделить символы
                tokens = alt.strip().split()
                if not tokens: 
                    tokens = ['ε'] 
                
                clean_tokens = []
                for t in tokens:
                    # Обработка разных вариантов записи эпсилон
                    if t.lower() in ['eps', 'epsilon', 'ε', 'lambda']:
                        clean_tokens.append('') 
                    else:
                        clean_tokens.append(t)
                
                # Если правило пустая строка -> сохраняем как []
                if len(clean_tokens) == 1 and clean_tokens[0] == '':
                    self.rules[lhs].append([])
                else:
                    self.rules[lhs].append(clean_tokens)
        
        self.start_symbol = first_symbol
        self.update_vocab()
        
        if not self.start_symbol:
            raise ValueError("Грамматика пуста.")

    def update_vocab(self):
        self.non_terminals = set(self.rules.keys())
        self.terminals = set()
        for prod_list in self.rules.values():
            for prod in prod_list:
                for symbol in prod:
                    if symbol and symbol not in self.non_terminals:
                        self.terminals.add(symbol)

    def is_valid(self):
        if not self.start_symbol: return False, "Нет стартового символа."
        if self.start_symbol not in self.rules: return False, "Стартовый символ не имеет правил."
        return True, "Грамматика корректна."

    def __str__(self):
        res = []
        for nt in sorted(self.rules.keys()):
            prods = []
            for p in self.rules[nt]:
                prods.append(' '.join(p) if p else 'ε')
            res.append(f"{nt} -> {' | '.join(prods)}")
        return "\n".join(res)

class CNFConverter:
    """Класс для приведения к Нормальной Форме Хомского."""
    @staticmethod
    def to_cnf(cfg_input):
        cfg = copy.deepcopy(cfg_input)
        
        # 1. Новый стартовый символ
        new_start = "S0"
        while new_start in cfg.rules: new_start += "_"
        cfg.rules[new_start] = [[cfg.start_symbol]]
        cfg.start_symbol = new_start
        cfg.update_vocab()

        # 2. Устранение терминалов в длинных правилах (TERM)
        term_map = {} 
        new_rules = {}
        for nt, prods in cfg.rules.items():
            new_prods = []
            for prod in prods:
                if len(prod) > 1:
                    new_prod = []
                    for sym in prod:
                        if sym in cfg.terminals:
                            if sym not in term_map:
                                new_var = f"T_{sym}"
                                k = 0
                                while new_var in cfg.rules or new_var in new_rules:
                                    new_var = f"T_{sym}{k}"
                                    k += 1
                                term_map[sym] = new_var
                                new_rules[new_var] = [[sym]]
                            new_prod.append(term_map[sym])
                        else:
                            new_prod.append(sym)
                    new_prods.append(new_prod)
                else:
                    new_prods.append(prod)
            cfg.rules[nt] = new_prods
        cfg.rules.update(new_rules)
        cfg.update_vocab()

        # 3. Разбиение длинных правил (BIN)
        counter = 1
        nts = list(cfg.rules.keys())
        for nt in nts:
            prods = cfg.rules[nt]
            new_prods_for_nt = []
            for prod in prods:
                if len(prod) > 2:
                    curr_nt = nt
                    curr_rhs = prod
                    while len(curr_rhs) > 2:
                        first, rest = curr_rhs[0], curr_rhs[1:]
                        helper_nt = f"C{counter}"
                        counter += 1
                        if curr_nt == nt: new_prods_for_nt.append([first, helper_nt])
                        else: cfg.rules[curr_nt] = [[first, helper_nt]]
                        curr_nt = helper_nt
                        curr_rhs = rest
                    cfg.rules[curr_nt] = [curr_rhs]
                else:
                    new_prods_for_nt.append(prod)
            cfg.rules[nt] = new_prods_for_nt
        cfg.update_vocab()

        # 4. Удаление эпсилон-правил (DEL)
        nullable = set()
        while True:
            prev_len = len(nullable)
            for nt, prods in cfg.rules.items():
                for prod in prods:
                    if not prod or all(s in nullable for s in prod):
                        nullable.add(nt)
            if len(nullable) == prev_len: break
        
        for nt, prods in cfg.rules.items():
            new_set = set()
            for prod in prods:
                if not prod: continue
                # Генерируем все подмножества
                candidates = [[]]
                for sym in prod:
                    next_cands = []
                    for c in candidates:
                        next_cands.append(c + [sym])
                        if sym in nullable: next_cands.append(c)
                    candidates = next_cands
                for c in candidates:
                    if c: new_set.add(tuple(c))
            cfg.rules[nt] = [list(x) for x in new_set]
        
        if cfg.start_symbol in nullable:
            cfg.rules[cfg.start_symbol].append([])

        # 5. Удаление цепных правил (UNIT)
        unit_pairs = []
        for nt in cfg.rules:
            visited, queue = {nt}, [nt]
            while queue:
                curr = queue.pop(0)
                if curr != nt: unit_pairs.append((nt, curr))
                if curr in cfg.rules:
                    for prod in cfg.rules[curr]:
                        if len(prod) == 1 and prod[0] in cfg.non_terminals:
                            if prod[0] not in visited:
                                visited.add(prod[0])
                                queue.append(prod[0])
        
        for (A, B) in unit_pairs:
            if B in cfg.rules:
                for prod in cfg.rules[B]:
                    if len(prod) == 1 and prod[0] in cfg.non_terminals: continue
                    if prod not in cfg.rules[A]: cfg.rules[A].append(prod)
        
        for nt in cfg.rules:
            cfg.rules[nt] = [p for p in cfg.rules[nt] if not (len(p)==1 and p[0] in cfg.non_terminals)]

        # 6. Удаление бесполезных (USELESS)
        # Generating
        generating = set()
        while True:
            prev = len(generating)
            for nt, prods in cfg.rules.items():
                for prod in prods:
                    if all(s in cfg.terminals or s in generating for s in prod):
                        generating.add(nt); break
            if len(generating) == prev: break
        
        cfg.rules = {nt: [p for p in prods if all(s in cfg.terminals or s in generating for s in p)] 
                     for nt, prods in cfg.rules.items() if nt in generating}
        
        # Reachable
        if cfg.start_symbol in cfg.rules:
            reachable, queue = {cfg.start_symbol}, [cfg.start_symbol]
            while queue:
                curr = queue.pop(0)
                if curr in cfg.rules:
                    for prod in cfg.rules[curr]:
                        for s in prod:
                            if s in cfg.non_terminals and s not in reachable:
                                reachable.add(s); queue.append(s)
            cfg.rules = {k: v for k, v in cfg.rules.items() if k in reachable}
        else:
            cfg.rules = {} # Пустая грамматика

        cfg.update_vocab()
        return cfg

class LanguageGenerator:
    """Генератор цепочек языка."""
    @staticmethod
    def generate(cfg, min_len, max_len):
        results = set()
        # Очередь: (текущая форма списка, длина терминалов в ней)
        queue = [([cfg.start_symbol], 0)]
        steps = 0
        MAX_STEPS = 50000 # Защита от зависания
        
        while queue and steps < MAX_STEPS:
            steps += 1
            curr_form, term_len = queue.pop(0)
            
            if term_len > max_len: continue
            
            # Ищем первый нетерминал
            nt_idx = -1
            for i, sym in enumerate(curr_form):
                if sym in cfg.rules:
                    nt_idx = i
                    break
            
            # Если нетерминалов нет - это слово
            if nt_idx == -1:
                word = "".join(curr_form)
                if min_len <= len(word) <= max_len:
                    results.add(word)
                continue
            
            # Раскрываем нетерминал
            nt = curr_form[nt_idx]
            prefix = curr_form[:nt_idx]
            suffix = curr_form[nt_idx+1:]
            
            for prod in cfg.rules.get(nt, []):
                new_form = prefix + prod + suffix
                # Считаем новую длину терминальной части (оптимизация)
                new_term_len = 0
                for s in new_form:
                    if s not in cfg.rules: new_term_len += len(s)
                
                if new_term_len <= max_len:
                    queue.append((new_form, new_term_len))
                    
        return sorted(list(results))

# ==========================================
# ЧАСТЬ 2: ГРАФИЧЕСКИЙ ИНТЕРФЕЙС (TKINTER)
# ==========================================

class GrammarApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Приведение КС-грамматики к НФХ и проверка эквивалентности")
        self.root.geometry("1000x800")
        
        self.cfg = CFG()
        self.cnf = None
        
        self.setup_menu()
        self.setup_ui()

    def setup_menu(self):
        menubar = tk.Menu(self.root)
        
        # Меню "Файл"
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Сохранить результаты...", command=self.save_to_file)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.root.quit)
        menubar.add_cascade(label="Файл", menu=file_menu)
        
        # Меню "Действия"
        action_menu = tk.Menu(menubar, tearoff=0)
        action_menu.add_command(label="Преобразовать в НФХ", command=self.convert_grammar)
        action_menu.add_command(label="Сравнить языки (Генерация)", command=self.generate_and_compare_ui_call)
        menubar.add_cascade(label="Расчёты", menu=action_menu)
        
        # Меню "Справка"
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Автор", command=self.show_author)
        help_menu.add_command(label="Тема задания", command=self.show_topic)
        help_menu.add_separator()
        help_menu.add_command(label="Формат ввода", command=self.show_help)
        menubar.add_cascade(label="Справка", menu=help_menu)
        
        self.root.config(menu=menubar)

    def setup_ui(self):
        # Панель ввода
        input_frame = ttk.LabelFrame(self.root, text="Ввод грамматики и параметров", padding=10)
        input_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Текстовое поле для грамматики
        lbl_gram = ttk.Label(input_frame, text="Грамматика (S -> A B | a):")
        lbl_gram.pack(anchor=tk.W)
        self.txt_grammar = scrolledtext.ScrolledText(input_frame, height=8, width=100)
        self.txt_grammar.pack(fill=tk.X, pady=5)
        self.txt_grammar.insert(tk.END, "S -> A S B | ε\nA -> a A S | a\nB -> S b S | A | b b") # Пример

        # Параметры длин
        params_frame = ttk.Frame(input_frame)
        params_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(params_frame, text="Мин. длина цепочки:").pack(side=tk.LEFT)
        self.ent_min = ttk.Entry(params_frame, width=5)
        self.ent_min.insert(0, "1")
        self.ent_min.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(params_frame, text="Макс. длина цепочки:").pack(side=tk.LEFT)
        self.ent_max = ttk.Entry(params_frame, width=5)
        self.ent_max.insert(0, "5")
        self.ent_max.pack(side=tk.LEFT, padx=5)
        
        # Кнопки быстрого доступа
        btn_frame = ttk.Frame(input_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="1. Преобразовать в НФХ", command=self.convert_grammar).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="2. Генерировать цепочки", command=self.generate_and_compare_ui_call).pack(side=tk.LEFT, padx=5)
        
        # Основная рабочая область (Вкладки)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Вкладка 1: Результат НФХ
        self.tab_cnf = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_cnf, text="Нормальная Форма Хомского")
        self.txt_cnf = scrolledtext.ScrolledText(self.tab_cnf, state='disabled', font=("Consolas", 10))
        self.txt_cnf.pack(fill=tk.BOTH, expand=True)
        
        # Вкладка 2: Сравнение множеств
        self.tab_verify = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_verify, text="Проверка эквивалентности")
        
        ver_lbl = ttk.Label(self.tab_verify, text="Ниже представлены сгенерированные множества. Вы можете вручную изменить их (удалить/добавить строки), чтобы проверить работу сравнения.", foreground="blue", wraplength=900)
        ver_lbl.pack(pady=5)
        
        sets_pane = ttk.PanedWindow(self.tab_verify, orient=tk.HORIZONTAL)
        sets_pane.pack(fill=tk.BOTH, expand=True)
        
        # Левый список (Исходная)
        f1 = ttk.LabelFrame(sets_pane, text="Множество 1 (Исходная КС-грамматика)")
        sets_pane.add(f1, weight=1)
        self.txt_set1 = scrolledtext.ScrolledText(f1, width=40)
        self.txt_set1.pack(fill=tk.BOTH, expand=True)
        
        # Правый список (НФХ)
        f2 = ttk.LabelFrame(sets_pane, text="Множество 2 (НФХ)")
        sets_pane.add(f2, weight=1)
        self.txt_set2 = scrolledtext.ScrolledText(f2, width=40)
        self.txt_set2.pack(fill=tk.BOTH, expand=True)
        
        # Кнопка сравнения и результат
        compare_frame = ttk.Frame(self.tab_verify, padding=5)
        compare_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        ttk.Button(compare_frame, text="Сравнить текущие множества", command=self.compare_sets_action).pack(side=tk.TOP, pady=5)
        self.lbl_result = ttk.Label(compare_frame, text="Статус: Ожидание", font=("Arial", 10, "bold"))
        self.lbl_result.pack(side=tk.TOP)
        self.txt_diff = scrolledtext.ScrolledText(compare_frame, height=6)
        self.txt_diff.pack(fill=tk.X, pady=5)

    # --- Обработчики событий ---

    def show_author(self):
        messagebox.showinfo("Автор", "Студент: Оганесян А.С.\nГруппа: ИП-211")

    def show_topic(self):
        msg = ("Тема задания №11:\n"
               "Разработать программу преобразования КС-грамматики в НФХ.\n"
               "Проверить эквивалентность путем генерации цепочек заданной длины.\n"
               "Реализовать возможность ручного редактирования множеств для тестирования.")
        messagebox.showinfo("Тема", msg)

    def show_help(self):
        msg = ("Формат ввода:\n"
               "S -> A B | a\n"
               "A -> b | ε\n\n"
               "ВАЖНО:\n"
               "- Разделяйте ВСЕ символы пробелами (A B, а не AB).\n"
               "- Нетерминалы - только заглавные буквы.\n"
               "- Пустая строка: 'eps', 'epsilon', 'ε' или просто пустота.")
        messagebox.showinfo("Справка", msg)

    def convert_grammar(self):
        raw_text = self.txt_grammar.get("1.0", tk.END)
        try:
            self.cfg.parse_from_text(raw_text)
            self.cnf = CNFConverter.to_cnf(self.cfg)
            
            self.txt_cnf.config(state='normal')
            self.txt_cnf.delete("1.0", tk.END)
            self.txt_cnf.insert(tk.END, str(self.cnf))
            self.txt_cnf.config(state='disabled')
            
            self.notebook.select(self.tab_cnf)
            messagebox.showinfo("Успех", "Преобразование в НФХ выполнено!")
            return True
        except Exception as e:
            messagebox.showerror("Ошибка парсинга/конвертации", str(e))
            return False

    def generate_and_compare_ui_call(self):
        # Сначала пробуем конвертировать, если еще не сделали
        if not self.convert_grammar(): 
            return

        try:
            mn = int(self.ent_min.get())
            mx = int(self.ent_max.get())
            if mn < 0 or mx < mn: raise ValueError("Некорректный диапазон.")
        except ValueError:
            messagebox.showerror("Ошибка", "Проверьте числа диапазона длин.")
            return

        # Генерация
        try:
            set1 = LanguageGenerator.generate(self.cfg, mn, mx)
            set2 = LanguageGenerator.generate(self.cnf, mn, mx)
            
            # Заполняем поля для редактирования
            self.txt_set1.delete("1.0", tk.END)
            self.txt_set1.insert(tk.END, "\n".join(set1))
            
            self.txt_set2.delete("1.0", tk.END)
            self.txt_set2.insert(tk.END, "\n".join(set2))
            
            self.notebook.select(self.tab_verify)
            
            # Сразу запускаем сравнение
            self.compare_sets_action()
            
        except Exception as e:
            messagebox.showerror("Ошибка генерации", str(e))

    def compare_sets_action(self):
        """Читает текущее содержимое текстовых полей и сравнивает."""
        # Читаем из GUI (пользователь мог изменить)
        s1_raw = self.txt_set1.get("1.0", tk.END).strip().split('\n')
        s2_raw = self.txt_set2.get("1.0", tk.END).strip().split('\n')
        
        # Убираем пустые строки, которые могли возникнуть при копипасте
        set1 = set(s for s in s1_raw if s.strip() != "")
        set2 = set(s for s in s2_raw if s.strip() != "")
        
        diff1 = set1 - set2 # Есть в 1, нет в 2
        diff2 = set2 - set1 # Есть в 2, нет в 1
        
        self.txt_diff.delete("1.0", tk.END)
        
        if not diff1 and not diff2:
            self.lbl_result.config(text="РЕЗУЛЬТАТ: Множества ЭКВИВАЛЕНТНЫ", foreground="green")
            self.txt_diff.insert(tk.END, "Различий не найдено.")
        else:
            self.lbl_result.config(text="РЕЗУЛЬТАТ: Множества РАЗЛИЧАЮТСЯ", foreground="red")
            report = []
            if diff1:
                report.append(f"Есть в Исходной, но нет в НФХ ({len(diff1)} шт): {list(diff1)[:10]}...")
            if diff2:
                report.append(f"Есть в НФХ, но нет в Исходной ({len(diff2)} шт): {list(diff2)[:10]}...")
            self.txt_diff.insert(tk.END, "\n".join(report))

    def save_to_file(self):
        content = []
        content.append("=== ИСХОДНАЯ ГРАММАТИКА ===")
        content.append(self.txt_grammar.get("1.0", tk.END).strip())
        content.append("\n=== НФХ ===")
        content.append(self.txt_cnf.get("1.0", tk.END).strip())
        content.append("\n=== РЕЗУЛЬТАТЫ ПРОВЕРКИ ===")
        content.append(f"Диапазон: {self.ent_min.get()} - {self.ent_max.get()}")
        content.append(f"Статус: {self.lbl_result.cget('text')}")
        content.append("\nДетали различий:")
        content.append(self.txt_diff.get("1.0", tk.END).strip())
        
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", 
                                                 filetypes=[("Text files", "*.txt")])
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(content))
                messagebox.showinfo("Сохранение", "Файл успешно сохранен.")
            except Exception as e:
                messagebox.showerror("Ошибка сохранения", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    # Настройка стиля
    style = ttk.Style()
    style.theme_use('clam') 
    
    app = GrammarApp(root)
    root.mainloop()