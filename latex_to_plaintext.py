import pydetex.pipelines as pi

def latex_to_text(text):
  text = pi.strict_eqn(text)
  return text

if __name__ == '__main__':
  path = "test.tex"
  with open(path, 'r') as file:
    text = file.read()
  print(latex_to_text(text))