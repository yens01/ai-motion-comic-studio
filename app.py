import streamlit as st
from PIL import Image
from io import BytesIO
import zipfile

st.set_page_config(page_title='AI Motion Comic Studio', layout='wide')
st.title('🎬 AI Motion Comic Studio')
st.caption('MVP: upload a comic, manually crop panels, export panel images. Use only assets you have rights to use.')
file = st.file_uploader('Upload comic page', type=['png','jpg','jpeg'])
if file:
    image = Image.open(file).convert('RGB')
    st.image(image, caption=f'Original page ({image.width} × {image.height})', use_container_width=True)
    st.write('Enter crop coordinates (pixels): left, top, right, bottom')
    count = st.number_input('Number of panels', min_value=1, max_value=20, value=3)
    crops=[]
    for i in range(count):
        with st.expander(f'Panel {i+1}', expanded=i==0):
            a,b,c,d=st.columns(4)
            left=a.number_input('Left',0,image.width-1,0,key=f'l{i}')
            top=b.number_input('Top',0,image.height-1,0,key=f't{i}')
            right=c.number_input('Right',1,image.width,image.width,key=f'r{i}')
            bottom=d.number_input('Bottom',1,image.height,image.height,key=f'b{i}')
            if right>left and bottom>top:
                crop=image.crop((left,top,right,bottom))
                st.image(crop,width=260)
                crops.append((f'panel_{i+1:02}.png',crop))
            else: st.error('Right must exceed left; bottom must exceed top')
    if len(crops)==count:
        buffer=BytesIO()
        with zipfile.ZipFile(buffer,'w') as z:
            for name,crop in crops:
                out=BytesIO();crop.save(out,format='PNG');z.writestr(name,out.getvalue())
        st.download_button('Download cropped panels (ZIP)',buffer.getvalue(),'panels.zip','application/zip')
