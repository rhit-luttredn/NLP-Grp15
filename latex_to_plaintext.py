import pydetex.pipelines as pi

file_path = "test.tex"

def latex_to_text(path):
  with open(path, 'r') as file:
    content = file.read()
  text = pi.strict_eqn(content)
  return text

print(latex_to_text(file_path))