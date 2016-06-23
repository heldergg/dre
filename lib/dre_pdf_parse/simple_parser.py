# -*- coding: utf-8 -*-

'''
Tokenizer, lexer and parser - generic
'''

##
# Imports
##

import re

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
                 post_massage_rules,
                 parser_transitions = []):
        self.pre_massage_rules = pre_massage_rules
        self.post_massage_rules = post_massage_rules
        self.split_rules = tokenizer_rules['split_rules']
        self.merge_rules = tokenizer_rules['merge_rules']
        self.lexicon = lexicon
        self.parser_rules = parser_rules
        self.parser_transitions = parser_transitions
        self.state = {}

    # Utils
    def clean_state(self):
        self.state = {}

    def state_setup(self):
        '''
        Initializes the state property
        '''
        pass

    # Massager
    def massager(self, txt, rules):
        for pattern, replace in rules:
            txt = re.sub(pattern, replace, txt)
        return txt

    # Tokenizer
    def set_tokenizer_state(self, tok_ord, token):
        '''
        The tokenizer line merging gets a state argument. The state can be
        defined on this method.
        '''
        pass

    def tokens(self, txt):
        return (token.strip()
                for token in re.split(self.split_rules, txt)
                if token)

    def tokenizer(self, txt):
        first_token = self.tokens(txt).next()
        self.state['t'] = []
        tok_ord = 0
        for i, token in enumerate(self.tokens(txt)):
            for first_test, second_text, rule in self.merge_rules:
                if (first_test(first_token, self.state) and
                        second_text(token, self.state)):
                    token = u' '.join((first_token, token))
                    first_token = token
                    break
            if first_token != token:
                yield first_token
                tok_ord += 1
                self.set_tokenizer_state(tok_ord, first_token)
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
    def set_parser_state(self, t_type, text):
        '''
        The rule dispatch callback gets a state parameter. This parameter can
        be defined in this method.
        '''
        pass

    def rule_dispatch(self, t_type, template, text, state ):
        return template % text

    def transition_dispatch(self, t_type_0, t_type_1, template, state):
        return template

    def manage_transitions(self, t_type_0, t_type_1):
        for text0_re, text1_re, template in self.parser_transitions:
            # TODO: pre-compile these regexes
            if re.match(text0_re,t_type_0) and re.match(text1_re,t_type_1):
                return self.transition_dispatch(t_type_0, t_type_1,
                        template, self.state)
        return ''

    def parser(self, tokens):
        html = []
        old_t_type = ''
        for t_type, text in tokens:
            self.set_parser_state(t_type, text)
            template = self.parser_rules[t_type]
            transition = self.manage_transitions(old_t_type, t_type)
            if transition:
                html.append(transition)
            parsed_tok = self.rule_dispatch(t_type, template, text, self.state)
            html.append(parsed_tok)
            old_t_type = t_type
        return u'\n'.join(html)

    # Main
    def run(self, txt):
        self.state_setup()
        txt = self.massager(txt, self.pre_massage_rules)
        tokens = self.tokenizer(txt)
        tokens = self.lexer(tokens)
        parsed = self.parser(tokens)
        parsed = self.massager(parsed, self.post_massage_rules)
        self.clean_state()
        return parsed
