import re
import logging

logger = logging.getLogger(__name__)

def extract_string(some_input):
    """ parses a string or a one-element list of strings into a string
        this is a utility function to help other parsing functions have more input flexibility
    """
    if isinstance(some_input, list):
        assert len(some_input) == 1
        first_item = some_input[0]
        assert isinstance(first_item, str)
        return first_item
    elif isinstance(some_input, str):
        return some_input
    else:
        raise AssertionError # not one-element list of strings or string

def parse_county_state(county_state):
    """ @input county_state string in the form '[countyName] County, [stateAbbr.]' """
    to_parse = county_state.lower()
    for x in ["county,", "parish,", "borough,"]:
        if x in to_parse:
            cs = to_parse.split(x)
            return cs[0].strip().title(), parse_state(cs[1])
    logger.warning("county not found: " + county_state)
    return None, None

def clean_text(string):
    return string.strip()

def parse_state(state):
    """ 
        returns the two-letter abbreviation for the given state. 
        State is always a string, but may be the full state name or the two-letter abbreviation
    """
    state = state.strip()
    if len(state) == 2:
        state = state.upper()
        assert state in state_abbr.values(), 'not a state: ' + str(state)
        return state
    else:
        state = state.title()
        assert state in state_abbr.keys(), 'not a state: ' + str(state)
        return state_abbr[state]

def parse_township(string):
    """ @input county_state string in the form '[township_name] Township, ...' 
        NOTE: the township name must be the first word(s) in the input string
    """
    return string.lower().split(' township')[0].title()

html_cleaner = re.compile('<.*?>')
def clean_html(raw_html):
    """ removes all html tags from a string """
    return re.sub(html_cleaner, '', raw_html)

def parse_html(html_string):
    """ extracts a nicely-formatted string from raw html
        input:
            '<td>\n
                Hinnerk Wolters
                <a href="mailto:hinnerkwolters@hagemanrealty.com">hinnerkwolters@hagemanrealty.com</a>
                <a href="tel:(219)%20261-2000">(219) 261-2000</a>
            </td>'
        output: 'Hinnerk Wolters hinnerkwolters@hagemanrealty.com (219) 261-2000'
    """
    return clean_whitespace(clean_html(html_string))

def clean_whitespace(a_string):
    """ removes excessive whitespace from a string. adds newline characters to keep spacing """
    return re.sub(r'\s\s+', ' ', re.sub(r'\s', ' ', a_string)).strip()

def parse_acres(f):
    return parse_num(f)

def parse_tax_id(t):
    """ input:  #123-456-7899 
        output: 123456789
    """
    return parse_num(t.replace("#",'').replace('-','').replace('.','').strip())


def parse_num(a_string):
    """ extract number from a string
        raises AssertionError if multiple numbers
    """
    nums = parse_nums(a_string)
    assert len(nums) == 1, "multiple numbers in string: " + a_string
    return nums[0]

def parse_nums(a_string):
    """ extract numbers from a string """
    return [float(x) for x in re.findall(r"[-+]?\d*\.\d+|\d+", a_string.replace(',',''))]

def parse_price(a_string):
    """ return the price from the string, if it exists """
    assert '$' in a_string

    split_string = a_string.split('$')
    assert len(split_string) == 2, 'multiple prices in string: ' + a_string
    return parse_nums(split_string[1])[0]

    # TODO handle common errors
    # elif 'call for price' in a_string:
    # elif 'sold'
    # elif 'auction'


def parse_latlong(latlong):
    """ latlong is a string of the form '+/-x.xxxxx, +/-y.yyyyy"""
    [float(x) for x in latlong.split(',')]


state_abbr = {
    'Alabama': 'AL',
    'Alaska': 'AK',
    'Arizona': 'AZ',
    'Arkansas': 'AR',
    'California': 'CA',
    'Colorado': 'CO',
    'Connecticut': 'CT',
    'Delaware': 'DE',
    'Florida': 'FL',
    'Georgia': 'GA',
    'Hawaii': 'HI',
    'Idaho': 'ID',
    'Illinois': 'IL',
    'Indiana': 'IN',
    'Iowa': 'IA',
    'Kansas': 'KS',
    'Kentucky': 'KY',
    'Louisiana': 'LA',
    'Maine': 'ME',
    'Maryland': 'MD',
    'Massachusetts': 'MA',
    'Michigan': 'MI',
    'Minnesota': 'MN',
    'Mississippi': 'MS',
    'Missouri': 'MO',
    'Montana': 'MT',
    'Nebraska': 'NE',
    'Nevada': 'NV',
    'New Hampshire': 'NH',
    'New Jersey': 'NJ',
    'New Mexico': 'NM',
    'New York': 'NY',
    'North Carolina': 'NC',
    'North Dakota': 'ND',
    'Ohio': 'OH',
    'Oklahoma': 'OK',
    'Oregon': 'OR',
    'Pennsylvania': 'PA',
    'Rhode Island': 'RI',
    'South Carolina': 'SC',
    'South Dakota': 'SD',
    'Tennessee': 'TN',
    'Texas': 'TX',
    'Utah': 'UT',
    'Vermont': 'VT',
    'Virginia': 'VA',
    'Washington': 'WA',
    'West Virginia': 'WV',
    'Wisconsin': 'WI',
    'Wyoming': 'WY',
}

def highlight(a_string, term):
    """ highlights term in a_string -- used for highlighting terminal output """
    return a_string.replace(term, '\033[1;32;40m'+term+'\033[0m')

def get_county_type(state):
    """ returns the type of county-level subdivision for each state
        returns Parish for Louisiana, Borough for Alaska, and County for everything else
        @input state must be a state string
    """
    state = parse_state(state)
    state_to_type = {'LA': 'Parish', 'AK': 'Borough'}
    return state_to_type[state] if state in state_to_type else 'County'