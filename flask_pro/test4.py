"""
scp -r C:\Users\Morning\Desktop\hiwi\ttl_query\flask_pro\app_changed_multi.py TUM_LfK@10.162.94.1:D:\puzhen\hi_structure\ttl_query\flask_pro

scp -r C:\Users\Morning\Desktop\hiwi\ttl_query\flask_pro\rag_model.py TUM_LfK@10.162.94.1:D:\puzhen\hi_structure\ttl_query\flask_pro
scp -r C:\Users\Morning\Desktop\hiwi\ttl_query\flask_pro\rag_model_openai.py TUM_LfK@10.162.94.1:D:\puzhen\hi_structure\ttl_query\flask_pro
scp -r C:\Users\Morning\Desktop\hiwi\ttl_query\geo_functions.py TUM_LfK@10.162.94.1:D:\puzhen\hi_structure\ttl_query\flask_pro
scp -r C:\Users\Morning\Desktop\hiwi\ttl_query\bounding_box.py TUM_LfK@10.162.94.1:D:\puzhen\hi_structure\ttl_query\flask_pro

scp -r C:\Users\Morning\Desktop\hiwi\ttl_query\flask_pro\chat_py.py TUM_LfK@10.162.94.1:D:\puzhen\hi_structure\ttl_query\flask_pro
scp -r C:\Users\Morning\Desktop\hiwi\ttl_query\flask_pro\ask_functions_agent.py TUM_LfK@10.162.94.1:D:\puzhen\hi_structure\ttl_query\flask_pro
scp -r C:\Users\Morning\Desktop\hiwi\ttl_query\flask_pro\app_changed_agent.py TUM_LfK@10.162.94.1:D:\puzhen\hi_structure\ttl_query\flask_pro
scp -r C:\Users\Morning\Desktop\hiwi\ttl_query\geo_functions.py TUM_LfK@10.162.94.1:D:\puzhen\hi_structure\ttl_query\flask_pro
scp -r C:\Users\Morning\Desktop\hiwi\ttl_query\flask_pro\rag_contriever.py TUM_LfK@10.162.94.1:D:\puzhen\hi_structure\ttl_query\flask_pro
scp -r C:\Users\Morning\Desktop\hiwi\ttl_query\flask_pro\templates\index.html TUM_LfK@10.162.94.1:D:\puzhen\hi_structure\ttl_query\flask_pro\templates
ssh TUM_LfK@10.162.94.1
TUM_LfK_4080
D:
cd puzhen\hi_structure\ttl_query\flask_pro

conda activate puzhenenv
python app_changed_agent.py
python ask_functions_agent.py
"""
"""
land details\nfiltered_farmland_details\n']
#><;><;><; Munich
set_bounding_box("Munich")
#><;><;><; AAC
farmland_ids=id_list_of_entity('land which is farmland')
#><;><;><; Get the list of IDs for landuse good for planting potatoes
potato_landuse_ids = id_list_of_entity("good for planting potatoes")
#><;><;><; Filter the farmland IDs to find those good for planting potatoes
filtered_farmland_ids = geo_filter('on', potato_landuse_ids, farmland_ids)
#><;><;><; Ober
set_bounding_box("Oberschleissheim")


#><;><;><; Output the filtered farmland details

print(filtered_farmland_details)




time.sleep(4)
#><; Set the bounding box to Munich
set_bounding_box("Oberschleissheim")

#><; Get the id
engli = id_list_of_entity("land")




"""


