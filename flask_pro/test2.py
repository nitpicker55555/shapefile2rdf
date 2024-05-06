aa="""

aasdasdfasdfa
asdasdfd=asdasd
"""
aa=aa.split('\n')
# aa=[aa]
print(aa)
filtered_lst = [x for x in aa if x!='']
print(filtered_lst[-1])

variable_str = filtered_lst[-1].split('=')[0]
print(variable_str)