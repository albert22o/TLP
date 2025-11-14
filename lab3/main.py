import Parser as parser

# S -> aSb | e
grammar = {
    'S': [
        ['a', 'S', 'b'],  # Правило S -> aSb
        ['']              # Правило S -> эпсилон
    ]
}

pda1 = parser.Parser(grammar=grammar, start_terminal = 'S')

strings_to_check = [
    "",        
    "ab",      
    "aabb",    
    "a",       
    "abb",     
    "ba"       
]

for s in strings_to_check:
    pda1.parse(s)