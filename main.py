from github import Github
from github import Auth
# pip install PyGithub

#g = Github("kavi.seewoogoolam@gmail.com", "Ka.6113.vi")
#repo = g.get_user().get_repo( "pipelines" )
#print(repo.get_dir_contents(""))

auth = Auth.Token("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")

g = Github(auth=auth)

#g = Github(base_url="https://github.com/kavi106", auth=auth)
#print(g.get_organization)
#print(g.get_user().get_repos())

# Then play with your Github objects:
#for repo in g.get_user().get_repos():
#    print(repo.name)

#repo = g.get_user().get_repo( "pipelines" )
#for path in repo.get_contents(path = ""):
#    print(path.)
repo = g.get_repo("kavi106/pipelines")
contents = repo.get_contents("")
print(contents)
while contents:
    file_content = contents.pop(0)
    if file_content.type == "dir":
      contents.extend(repo.get_contents(file_content.path))
      #print(file_content.path)
    #else:
    #  print(file_content)


#print(repo.get_contents(path = ""))