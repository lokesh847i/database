# mtm_html.py
# File 18: HTML template combiner

from mtm_html_part1 import DASHBOARD_HTML_PART1
from mtm_html_part2 import DASHBOARD_HTML_PART2
from mtm_html_part3 import DASHBOARD_HTML_PART3
from mtm_html_part4 import DASHBOARD_HTML_PART4
from mtm_html_part5 import DASHBOARD_HTML_PART5
from mtm_html_part6 import DASHBOARD_HTML_PART6
from mtm_html_part7 import DASHBOARD_HTML_PART7
from mtm_html_part8 import DASHBOARD_HTML_PART8
from mtm_html_part9 import DASHBOARD_HTML_PART9

# Combine all HTML parts
DASHBOARD_HTML = (
    DASHBOARD_HTML_PART1 + 
    DASHBOARD_HTML_PART2 + 
    DASHBOARD_HTML_PART3 + 
    DASHBOARD_HTML_PART4 + 
    DASHBOARD_HTML_PART5 + 
    DASHBOARD_HTML_PART6 + 
    DASHBOARD_HTML_PART7 +
    DASHBOARD_HTML_PART8 +
    DASHBOARD_HTML_PART9
)
