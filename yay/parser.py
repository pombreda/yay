

from ply import yacc

from lexer import Lexer
from . import nodes
from . import ast

tokens = Lexer.tokens

start = 'node'

class ParseError(Exception):
    
    def __init__(self, token, lineno):
        self.token = token
        self.lineno = lineno
        
    def __str__(self):
        return "Syntax error at line %d: '%s'" % (self.lineno, self.token)

def p_error(p):
    raise ParseError(p.value, p.lineno)
    
    
########## EXPRESSIONS
## http://docs.python.org/2/reference/expressions.html

# Atoms are the most basic elements of expressions. The simplest atoms
# are identifiers or literals. Forms enclosed in reverse quotes or in
# parentheses, brackets or braces are also categorized syntactically as
# atoms.

def p_atom_identifier(p):
    '''
    atom : IDENTIFIER
    '''
    p[0] = ast.Identifier(p[1])
    
def p_atom_literal(p):
    '''
    atom : LITERAL
    '''
    p[0] = ast.Literal(p[1])

def p_atom_enclosure(p):
    '''
    atom : enclosure
    '''
    p[0] = p[1]
    
    
def p_enclosure(p):
    '''
    enclosure : parenth_form 
              | list_display
              | generator_expression
              | dict_display
              | set_display
              | string_conversion
    '''
    p[0] = p[1]

def p_parent_form(p):
    '''
    parenth_form : "(" ")"
                 | "(" expression_list ")"
    '''
    # A parenthesized form is an optional expression list enclosed in
    # parentheses
    # 
    # A parenthesized expression list yields whatever that expression list
    # yields: if the list contains at least one comma, it yields a tuple;
    # otherwise, it yields the single expression that makes up the expression
    # list.
    # 
    # An empty pair of parentheses yields an empty tuple object. Since tuples
    # are immutable, the rules for literals apply (i.e., two occurrences of
    # the empty tuple may or may not yield the same object).
    # 
    # Note that tuples are not formed by the parentheses, but rather by use
    # of the comma operator. The exception is the empty tuple, for which
    # parentheses are required - allowing unparenthesized "nothing" in
    # expressions would cause ambiguities and allow common typos to pass
    # uncaught.

    if len(p) == 3:
        p[0] = ast.ParentForm()
    else:
        p[0] = ast.ParentForm(p[2])
    
def p_list_display(p):
    '''
    list_display : "[" "]"
                 | "[" expression_list "]"
                 | "[" list_comprehension "]"
    '''
    # A list display is a possibly empty series of expressions enclosed in
    # square brackets.
    # 
    # A list display yields a new list object. Its contents are specified by
    # providing either a list of expressions or a list comprehension. When a
    # comma-separated list of expressions is supplied, its elements are
    # evaluated from left to right and placed into the list object in that
    # order. When a list comprehension is supplied, it consists of a single
    # expression followed by at least one for clause and zero or more for or
    # if clauses. In this case, the elements of the new list are those that
    # would be produced by considering each of the for or if clauses a block,
    # nesting from left to right, and evaluating the expression to produce a
    # list element each time the innermost block is reached.
    if len(p) == 3:
        p[0] = ast.ListDisplay()
    else:
        p[0] = ast.ListDisplay(p[2])
    
def p_list_comprehension(p):
    '''
    list_comprehension : expression list_for
    '''
    raise NotImplementedError
    
def p_list_for(p):
    '''
    list_for : FOR target_list IN old_expression_list
             | FOR target_list IN old_expression_list list_iter
    '''
    raise NotImplementedError
    
def p_old_expression_list(p):
    '''
    old_expression_list : old_expression
                        | old_expression_list "," old_expression
                        | old_expression_list "," old_expression ","
    '''
    if len(p) == 2:
        p[0] = ast.ExpressionList(p[1])
    else:
        p[0] = p[1]
        p[0].append(p[3])
    
def p_old_expression(p):
    '''
    old_expression : or_test 
                   | old_lambda_form
    '''
    p[0] = p[1]
    
def p_list_iter(p):
    '''
    list_iter : list_for
              | list_if
    '''
    raise NotImplementedError
    
def p_list_if(p):
    '''
    list_if : IF old_expression
            | IF old_expression list_iter
    '''
    raise NotImplementedError
    
def p_comprehension(p):
    '''
    comprehension : expression comp_for
    '''
    raise NotImplementedError
    
def p_comp_for(p):
    '''
    comp_for : FOR target_list IN or_test
             | FOR target_list IN or_test comp_iter
    '''
    raise NotImplementedError
    
def p_comp_iter(p):
    '''
    comp_iter : comp_for
              | comp_if
    '''
    raise NotImplementedError
    
def p_comp_if(p):
    '''
    comp_if : IF expression
            | IF expression comp_iter
    '''
    
    # expression is actually "expression_nocond" in the grammar
    # i do not know what this means
    # http://docs.python.org/2/reference/expressions.html#displays-for-sets-and-dictionaries
    raise NotImplementedError
    
def p_generator_expression(p):
    '''
    generator_expression : "(" expression comp_for ")"
    '''
    raise NotImplementedError
    
def p_dict_display(p):
    '''
    dict_display : "{" "}"
                 | "{" key_datum_list "}"
                 | "{" dict_comprehension "}"
    '''
    if len(p) == 3:
        p[0] = ast.DictDisplay()
    else:
        p[0] = ast.DictDisplay(p[2])
    
def p_key_datum_list(p):
    '''
    key_datum_list : key_datum
                   | key_datum_list "," key_datum
    '''
    if len(p) == 2:
        p[0] = ast.KeyDatumList(p[1])
    else:
        p[0] = p[1]
        p[0].append(p[3])
    
def p_key_datum(p):
    '''
    key_datum : expression ":" expression
    '''
    p[0] = ast.KeyDatum(p[1], p[3])

def p_dict_comprehension(p):
    '''
    dict_comprehension : expression ":" expression comp_for
    '''
    raise NotImplementedError

def p_set_display(p):
    '''
    set_display : "{" expression_list "}"
                | "{" comprehension "}"
    '''
    raise NotImplementedError
    
def p_string_conversion(p):
    '''
    string_conversion : "`" expression_list "`"
    '''
    raise NotImplementedError
    
def p_primary(p):
    '''
    primary : atom
            | attributeref
            | subscription
            | slicing
            | call
    '''
    p[0] = p[1]
    
def p_attributeref(p):
    '''
    attributeref : primary "." IDENTIFIER
    '''
    p[0] = ast.AttributeRef(p[1], p[3])
    
def p_subscription(p):
    '''
    subscription : primary "[" expression_list "]"
    '''
    p[0] = ast.Subscription(p[1], p[3])
    
def p_slicing(p):
    '''
    slicing : simple_slicing
            | extended_slicing
    '''
    p[0] = p[1]
    
def p_simple_slicing(p):
    '''
    simple_slicing : primary "[" short_slice "]"
    '''
    p[0] = ast.SimpleSlicing(p[1], p[3])
    
def p_extended_slicing(p):
    '''
    extended_slicing : primary "[" slice_list "]"
    '''
    p[0] = ast.ExtendedSlicing(p[1], p[3])
    
def p_slice_list(p):
    '''
    slice_list : slice_item
               | slice_list "," slice_item
               | slice_list "," slice_item ","
    '''
    if len(p) == 2:
        p[0] = ast.SliceList(p[1])
    else:
        p[0] = p[1]
        p[0].append(p[3])
    
def p_slice_item(p):
    '''
    slice_item : proper_slice
               | ELLIPSIS
    '''
    # removed expression as a production due to reduce/reduce conflict
    # subscription wins over slicing in the docs, so i think this is correct
    p[0] = p[1]
    
def p_proper_slice(p):
    '''
    proper_slice : short_slice
                 | long_slice
    '''
    p[0] = p[1]
    
def p_short_slice(p):
    '''
    short_slice : lower_bound ":"
                | ":" upper_bound
                | lower_bound ":" upper_bound
    '''
    if len(p) == 2:
        if p[2] == ':':
            lower_bound = p[1]
            upper_bound = None
        else:
            lower_bound = None
            upper_bound = p[2]
    else:
        lower_bound = p[1]
        upper_bound = p[3]
    p[0] = ast.Slice(lower_bound, upper_bound)
    
def p_long_slice(p):
    '''
    long_slice : short_slice ":"
               | short_slice ":" stride
    '''
    p[0] = p[1]
    if len(p) == 4:
        p[0].stride = p[3]
    
def p_lower_bound(p):
    '''
    lower_bound : expression
    '''
    p[0] = p[1]
    
def p_upper_bound(p):
    '''
    upper_bound : expression
    '''
    p[0] = p[1]
    
def p_stride(p):
    '''
    stride : expression
    '''
    p[0] = p[1]

def p_call(p):
    '''
    call : primary "(" ")"
         | primary "(" argument_list ")"
         | primary "(" argument_list "," ")"
    '''
    # some other stuff in here for genexpr_for that i don't grok
    if len(p) == 4:
        p[0] = ast.Call(p[1])
    else:
        p[0] = ast.Call(p[1], p[3])
    
def p_argument_list(p):
    '''
    argument_list : positional_arguments
                  | positional_arguments "," keyword_arguments
    '''
    # ignore all the * and ** stuff, don't think relevant
    if len(p) == 2:
        p[0] = ast.ArgumentList(p[1])
    else:
        p[0] = ast.ArgumentList(p[1], p[3])
    
    
def p_positional_arguments(p):
    '''
    positional_arguments : expression
                         | positional_arguments "," expression
    '''
    if len(p) == 2:
        p[0] = ast.PositionalArguments(p[1])
    else:
        p[0] = p[1]
        p[0].append(p[3])
    
def p_keyword_arguments(p):
    '''
    keyword_arguments : keyword_item
                      | keyword_arguments "," keyword_item
    '''
    if len(p) == 2:
        p[0] = ast.KeywordArguments(p[1])
    else:
        p[0] = p[1]
        p[0].append(p[3])
    
def p_keyword_item(p):
    '''
    keyword_item : IDENTIFIER "=" expression
    '''
    p[0] = ast.KeywordItem(p[1], p[3])
    
    
def p_power(p):
    '''
    power : primary
          | primary POW u_expr
    '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = ast.Power(p[1], p[3])

def p_u_expr(p):
    '''
    u_expr : power
           | "-" u_expr
           | "+" u_expr
           | "~" u_expr
    '''
    # The unary - (minus) operator yields the negation of its numeric
    # argument.
    # 
    # The unary + (plus) operator yields its numeric argument unchanged.
    # 
    # The unary ~ (invert) operator yields the bitwise inversion of its plain
    # or long integer argument. The bitwise inversion of x is defined as
    # -(x+1). It only applies to integral numbers.
    # 
    # In all three cases, if the argument does not have the proper type, a
    # TypeError exception is raised.
    if len(p) == 2:
        p[0] = p[1]
    else:
        if p[1] == '-':
            p[0] = ast.UnaryMinus(p[2])
        elif p[1] == '+':
            p[0] == p[2]
        elif p[1] == '~':
            p[0] = ast.Invert(p[2])
    
def p_m_expr(p):
    '''
    m_expr : u_expr
           | m_expr "*" u_expr
           | m_expr FLOOR_DIVIDE u_expr
           | m_expr "/" u_expr
           | m_expr "%" u_expr
    '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = ast.Expr(p[1], p[3], p[2])
    
    
def p_a_expr(p):
    '''
    a_expr : m_expr
           | a_expr "+" m_expr
           | a_expr "-" m_expr
    '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = ast.Expr(p[1], p[3], p[2])
    
def p_shift_expr(p):
    '''
    shift_expr : a_expr
               | shift_expr LSHIFT a_expr
               | shift_expr RSHIFT a_expr
    '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = ast.Expr(p[1], p[3], p[2])
    
def p_and_expr(p):
    '''
    and_expr : shift_expr
             | and_expr "&" shift_expr
    '''
    if len(p) ==2:
        p[0] = p[1]
    else:
        p[0] = ast.Expr(p[1], p[3], p[2])
    
def p_xor_expr(p):
    '''
    xor_expr : and_expr
             | xor_expr "^" and_expr
    '''
    if len(p) ==2:
        p[0] = p[1]
    else:
        p[0] = ast.Expr(p[1], p[3], p[2])
    
def p_or_expr(p):
    '''
    or_expr : xor_expr
            | or_expr "|" xor_expr
    '''
    if len(p) ==2:
        p[0] = p[1]
    else:
        p[0] = ast.Expr(p[1], p[3], p[2])
    
def p_comparison(p):
    '''
    comparison : or_expr 
               | or_expr comp_operator or_expr
    '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = ast.Expr(p[1], p[3], p[2])
    
def p_comp_operator(p):
    '''
    comp_operator : "<"
                  | ">"
                  | EQ
                  | GE
                  | LE
                  | GTLT
                  | NE
                  | IS
                  | IS NOT
                  | NOT
                  | NOT IN
    '''
    p[0] = " ".join(p[1:])
    
def p_or_test(p):
    '''
    or_test : and_test
            | or_test OR and_test
    '''
    if len(p) ==2:
        p[0] = p[1]
    else:
        p[0] = Expr(p[1], p[3], p[2])
    
def p_and_test(p):
    '''
    and_test : not_test
             | and_test AND not_test
    '''
    if len(p) ==2:
        p[0] = p[1]
    else:
        p[0] = Expr(p[1], p[3], p[2])
    
def p_not_test(p):
    '''
    not_test : comparison
             | NOT not_test
    '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = ast.Not(p[2])
    
def p_conditional_expression(p):
    '''
    conditional_expression : or_test
                           | or_test IF or_test ELSE expression
    '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = ast.ConditionalExpression(p[1], p[3], p[5])
        
def p_expression(p):
    '''
    expression : conditional_expression
               | lambda_form
    '''
    p[0] = p[1]
    
def p_lambda_form(p):
    '''
    lambda_form : LAMBDA ":" expression
                | LAMBDA parameter_list ":" expression
    '''
    raise NotImplementedError
    
def p_old_lambda_form(p):
    '''
    old_lambda_form : LAMBDA ":" expression
                    | LAMBDA parameter_list ":" old_expression
    '''
    raise NotImplementedError

def p_expression_list(p):
    '''
    expression_list : expression
                    | expression_list "," expression
                    | expression_list "," expression ","
    '''
    if len(p) == 2:
        p[0] = ast.ExpressionList(p[1])
    elif len(p) in (4,5):
        p[0] = p[1]
        p[0].append(p[3])

#### SIMPLE STATEMENTS
# http://docs.python.org/2/reference/simple_stmts.html

def p_target_list(p):
    '''
    target_list : target
                | target_list "," target
                | target_list "," target ","
    '''
    if len(p) == 2:
        p[0] = ast.TargetList(p[1])
    else:
        p[0] = p[1]
        p[0].append(p[3])
    
def p_target(p):
    '''
    target : IDENTIFIER
           | attributeref
           | subscription
           | slicing
    '''
    p[0] = p[1]

#### COMPOUND STATEMENTS
# http://docs.python.org/2/reference/compound_stmts.html

def p_parameter_list(p):
    '''
    parameter_list : defparameter
                   | parameter_list "," defparameter
                   | parameter_list "," defparameter ","
    '''
    if len(p) == 2:
        p[0] = ast.ParameterList(p[1])
    else:
        p[0] = p[1]
        p[0].append(p[3])
    
def p_defparameter(p):
    '''
    defparameter : parameter
                 | parameter "=" expression
    '''
    if len(p) == 2:
        p[0] = ast.DefParameter(p[1])
    else:
        p[0] = ast.DefParameter(p[1], p[3])
    
def p_parameter(p):
    '''
    parameter : IDENTIFIER
              | "(" sublist ")"
    '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = p[2]
    
def p_sublist(p):
    '''
    sublist : parameter
            | sublist "," parameter
            | sublist "," parameter ","
    '''
    if len(p) == 2:
        p[0] = ast.Sublist(p[1])
    else:
        p[0] = p[1]
        p[0].append(p[3])

#### yay \o/


def p_command(p):
    '''
    command : BLOCK '%' directive END
    '''
    p[0] = p[3]
    
def p_directive(p):
    '''
    directive : include_directive
              | search_directive
              | for_directive
              | set_directive
              | if_directive
              | select_directive
    '''
    p[0] = p[1]
    
def p_include_directive(p):
    '''
    include_directive : INCLUDE atom
    '''
    
def p_search_directive(p):
    '''
    search_directive : SEARCH atom
    '''
    
def p_for_directive(p):
    '''
    for_directive : FOR target IN atom node
                  | FOR target IF atom IN atom node
    '''
    
def p_set_directive(p):
    '''
    set_directive : SET target "=" expression
    '''
    p[0] = nodes.command.Set(p[2], p[4])
    
def p_if_directive(p):
    '''
    if_directive : IF atom node
                 | IF atom node ELSE node
                 | IF atom node elif_list
                 | IF atom node elif_list ELSE node
    '''
    
def p_elif_list(p):
    '''
    elif_list : elif
              | elif_list elif
    '''
    
def p_elif(p):
    '''
    elif : ELIF atom node
    '''
    
def p_select_directive(p):
    '''
    select_directive : SELECT atom case_list
    '''
    
def p_case_list(p):
    '''
    case_list : case_block
              | case_list case_block
    '''
    
def p_case_block(p):
    '''
    case_block : KEY ":" node
    '''
    
def p_command_node(p):
    'node : command'
    p[0] = p[1]

def p_node_scalar(p):
    'node : BLOCK SCALAR END'
    p[0] = nodes.Boxed(p[2])
    
def p_node_dict(p):
    'node : BLOCK dict END'
    m = nodes.Mapping()
    for key, value in p[2]:
        value.set_predecessor(m.get(key))
        m.set(key, value)
    p[0] = m
    
def p_node_list(p):
    'node : BLOCK list END'
    p[0] = nodes.Sequence(p[2])

def p_extend(p):
    'extend : EXTEND KEY node'
    p[0] = (p[2], nodes.Extend(p[3]))
    
def p_dict_extend(p):
    'dict : extend'
    p[0] = [(p[1][0], p[1][1])]
    
def p_dict_key_node(p):
    'dict : KEY node'
    p[0] = [(p[1], p[2])]
    
def p_dict_dict_dict(p):
    'dict : dict dict'
    p[1].extend(p[2])
    p[0] = p[1]

def p_dict_emptydict(p):
    'dict : EMPTYDICT'
    p[0] = nodes.Mapping()
    
def p_list_listitem_node(p):
    'list : LISTITEM node'
    p[0] = [p[2]]
    
def p_list_list_list(p):
    'list : list list'
    p[1].extend(p[2])
    p[0] = p[1]
    
def p_list_emptylist(p):
    'list : EMPTYLIST'
    p[0] = nodes.Sequence()
    
parser = yacc.yacc()

def parse(value):
    return parser.parse(value, lexer=Lexer())
