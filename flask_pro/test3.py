a= {"asd":'asdasd'}
graph_dict={}
graph_dict['primary_subject']='122'
element_list={}


for i in a:
    str_s="element_list['primary_subject']=graph_dict['primary_subject']\nprint(element_list)"

exec(str_s,globals())