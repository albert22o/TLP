import re

def parse_expression(s):
    s = s.replace(' ', '')
    tokens = re.findall(r'\d+|[a-zA-Z][a-zA-Z0-9]*|[+*/-]|\(|\)', s) + ['&']
    pos = [0]  
    
    def curr(): return tokens[pos[0]]
    def next_token(): pos[0] += 1
    
    def S():
        print('S ')
        T()
        E()
    
    def E():
        print('E ')
        if curr() in '+-':
            next_token()
            T()
            E()
    
    def T():
        print('T ')
        F()
        T_tail()
    
    def T_tail():
        print('T tail')
        if curr() in '*/':
            next_token()
            F()
            T_tail()

    def F():
        print('F ')
        if curr() == '(':
            next_token()
            S()
            if curr() != ')':
                raise Exception("Ожидалось ')'")
            next_token()
        elif re.match(r'^\d+$', curr()) or re.match(r'^[a-zA-Z]', curr()):
            next_token()
        else:
            raise Exception("Ожидалось number, id или '('")
    
    try:
        S()
        if curr() == '&':
            return "Выражение корректно"
        else:
            return "Ошибка: неожиданный конец выражения"
    except Exception as e:
        return f"Ошибка: {e}"

# Тестирование
test_cases = [
    "2 + 3 * 4",
    "a * (b - 10)",
    "5 + + 3",
    "(7 * 2"
]

for test in test_cases:
    result = parse_expression(test)
    print(f"'{test}' -> {result}")