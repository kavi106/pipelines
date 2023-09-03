from github import Github
from github import Auth

# pip install PyGithub
import json

# g = Github("kavi.seewoogoolam@gmail.com", "Ka.6113.vi")
# repo = g.get_user().get_repo( "pipelines" )
# print(repo.get_dir_contents(""))

auth = Auth.Token("xxx")

g = Github(auth=auth)

repo = g.get_repo("kavi106/pipelines")
try:
  contents = repo.get_contents("CSV Converter/datas.json")
  print(contents)
except:
  None
print("Done")
#print(contents.decoded_content.decode())

# g = Github(base_url="https://github.com/kavi106", auth=auth)
# print(g.get_organization)
# print(g.get_user().get_repos())

# Then play with your Github objects:
# for repo in g.get_user().get_repos():
#    print(repo.name)

# repo = g.get_user().get_repo( "pipelines" )
# for path in repo.get_contents(path = ""):
#    print(path.)
# repo = g.get_repo("kavi106/pipelines")
# contents = repo.get_contents("")
# contents = repo.get_contents("test.json")
# print(contents.decoded_content.decode())
# while contents:
#    file_content = contents.pop(0)
#    if file_content.type == "dir":
#      contents.extend(repo.get_contents(file_content.path))
# print(file_content.path)
# else:
#  print(file_content)


# print(repo.get_contents(path = ""))

# list of json objects
data_json = '{"name": "data", "age": 30}'
schema_json = '{"name": "schema", "age": 30}'
uischema_json = '{"name": "uischema", "age": 30}'

# Python dictionary
# dict = {
#     "Flow Cytometry": {
#         "schema": json.loads(schema_json),
#         "uischema": json.loads(uischema_json),
#         "data": json.loads(data_json),
#     }
# }
dict = {}
dict["Flow Cytometry"] = {}
dict["Flow Cytometry"]["schema"] = json.loads(schema_json)

#print(json.dumps(dict))
