from Fetch import Fetch
from Analytic import analyze_and_export_csv  as analyze
from Extract import get_comments_from_csv as get_comment

API_KEY = ""
Youtube_link = input("Youtube Link\n:")
file_name,total_comment = Fetch(API_KEY,Youtube_link)
comment_list = get_comment(file_name)
analyze(comment_list )
