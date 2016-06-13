# -*- coding: utf-8 -*-

'''
Tokenizer, lexer and parser - generic
'''

##
#  Lexer and parser
##

class SimpleParser(object):
    '''
    This is a simple yet complete parser. The arguments are:
        pre_massage_rules - list of tuples with replaces to be made on the
            text, before tokenization;
        tokenizer_rules - rules to tokenize the text. This is a dictionary
            containing two sets of rules:
            split_rules - its a regular expression to be used with re.split
            merge_rules - tuple with two functions, the first function if
                applied to the left token, the second one to the right
                token, if both return true the two tokens are merged
        lexicon - a lexicon to characterize the tokens
        parser_rules - dict with the output to be created for each
            definition on the lexicon
        post_massage_rules - replaces to be applied to the final output
    '''
    def __init__(self,
                 pre_massage_rules,
                 tokenizer_rules,
                 lexicon,
                 parser_rules,
                 post_massage_rules):
        self.pre_massage_rules = pre_massage_rules
        self.post_massage_rules = post_massage_rules
        self.split_rules = tokenizer_rules['split_rules']
        self.merge_rules = tokenizer_rules['merge_rules']
        self.lexicon = lexicon
        self.parser_rules = parser_rules

    # Massager
    def massager(self, txt, rules):
        for pattern, replace in rules:
            txt = re.sub(pattern, replace, txt)
        return txt

    # Tokenizer
    def tokens(self, txt):
        return (token.strip()
                for token in re.split(self.split_rules, txt)
                if token)

    def tokenizer(self, txt):
        first_token = self.tokens(txt).next()
        for token in self.tokens(txt):
            for first_test, second_text in self.merge_rules:
                if first_test(first_token) and second_text(token):
                    token = u' '.join((first_token, token))
                    first_token = token
                    break
            if first_token != token:
                yield first_token
                first_token = token
        yield token


    # Lexer
    def set_type(self, token):
        for t_type, test in self.lexicon:
            is_match = test(token)
            if is_match and t_type:
                return (t_type, token)
            elif is_match and not t_type:
                # Skip token
                break

    def lexer(self, tokens):
        for token in tokens:
            token = self.set_type(token)
            if token:
                yield token
    # Parser
    def parser(self, tokens):
        html = []
        for t_type, text in tokens:
            html.append(self.parser_rules[t_type] % text)
        return u'\n'.join(html)

    # Main
    def run(self, txt):
        txt = self.massager(txt, self.pre_massage_rules)
        tokens = self.tokenizer(txt)
        tokens = self.lexer(tokens)
        parsed = self.parser(tokens)
        parsed = self.massager(parsed, self.post_massage_rules)
        return parsed
