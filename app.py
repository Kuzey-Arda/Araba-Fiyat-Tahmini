import pandas as pd
import joblib
import gradio as gr

# pkl modelini yükle
try:
    pipe = joblib.load('car_price_model.pkl')
except FileNotFoundError:
    print("HATA: 'car_price_model.pkl' dosyası bulunamadı. Lütfen dosyanın doğru yolda olduğundan emin olun.")
    pipe = None # Model yüklenemezse None olarak ayarla
except Exception as e:
    print(f"Model yüklenirken bir hata oluştu: {e}")
    pipe = None

# Veri yükle
try:
    df = pd.read_excel('cars.xls')
    # Benzersiz değerleri ve NaN olmayanları alıp sıralamak, Gradio dropdown'ları için daha iyi
    make_options = sorted(df['Make'].dropna().unique().tolist())
    cylinder_options = sorted(df['Cylinder'].dropna().unique().tolist())
    doors_options = sorted(df['Doors'].dropna().unique().tolist())

except FileNotFoundError:
    print("HATA: 'cars.xls' dosyası bulunamadı. Lütfen dosyanın doğru yolda olduğundan emin olun.")
    # Örnek DataFrame veya boş DataFrame oluşturarak uygulamanın çökmesini engelle
    df = pd.DataFrame({
        'Make': [], 'Model': [], 'Trim': [], 'Type': [],
        'Cylinder': [], 'Doors': []
    })
    make_options = []
    cylinder_options = []
    doors_options = []
except Exception as e:
    print(f"Veri yüklenirken bir hata oluştu: {e}")
    df = pd.DataFrame({
        'Make': [], 'Model': [], 'Trim': [], 'Type': [],
        'Cylinder': [], 'Doors': []
    })
    make_options = []
    cylinder_options = []
    doors_options = []


def predict_price(make, model, trim, mileage, car_type, cylinder, liter, doors, cruise, sound, leather):
    if pipe is None:
        return "HATA: Model yüklenemedi, tahmin yapılamıyor."
    try:
        # Kullanıcıdan alınan verileri DataFrame'e dönüştür
        input_data = pd.DataFrame({
            'Make': [make],
            'Model': [model],
            'Trim': [trim],
            'Mileage': [mileage],
            'Type': [car_type],
            'Cylinder': [cylinder],
            'Liter': [liter],
            'Doors': [doors],
            'Cruise': [cruise],
            'Sound': [sound],
            'Leather': [leather]
        })
        prediction = pipe.predict(input_data)[0]
        return f"Tahmini Fiyat: ${int(prediction):,}" # Sayıyı formatla
    except Exception as e:
        return f"Tahmin sırasında bir hata oluştu: {e}"

# Dinamik olarak model seçeneklerini güncellemek için fonksiyon
def update_models(selected_make):
    if pd.isna(selected_make) or not selected_make: # Eğer marka seçilmemişse
        return gr.Dropdown(choices=[], label="Model", interactive=True, value=None)
    models = sorted(df[df['Make'] == selected_make]['Model'].dropna().unique().tolist())
    return gr.Dropdown(choices=models, label="Model", interactive=True, value=None if not models else models[0])

# Dinamik olarak donanım (trim) seçeneklerini güncellemek için fonksiyon
def update_trims(selected_make, selected_model):
    if pd.isna(selected_make) or not selected_make or pd.isna(selected_model) or not selected_model:
        return gr.Dropdown(choices=[], label="Donanım (Trim)", interactive=True, value=None)
    trims = sorted(df[(df['Make'] == selected_make) & (df['Model'] == selected_model)]['Trim'].dropna().unique().tolist())
    return gr.Dropdown(choices=trims, label="Donanım (Trim)", interactive=True, value=None if not trims else trims[0])

# Dinamik olarak araç tipi seçeneklerini güncellemek için fonksiyon
def update_types(selected_make, selected_model, selected_trim):
    if pd.isna(selected_make) or not selected_make or \
       pd.isna(selected_model) or not selected_model or \
       pd.isna(selected_trim) or not selected_trim:
        return gr.Dropdown(choices=[], label="Araç Tipi", interactive=True, value=None)
    types = sorted(df[(df['Make'] == selected_make) &
                      (df['Model'] == selected_model) &
                      (df['Trim'] == selected_trim)]['Type'].dropna().unique().tolist())
    return gr.Dropdown(choices=types, label="Araç Tipi", interactive=True, value=None if not types else types[0])


# Gradio arayüzü
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🚗 Fiyat Tahmin Uygulaması @drmurataltun")
    gr.Markdown("Araba fiyatı tahmini için aşağıdaki bilgileri giriniz:")

    with gr.Row():
        make_dd = gr.Dropdown(choices=make_options, label="Marka", interactive=True)
        model_dd = gr.Dropdown(choices=[], label="Model", interactive=True) # Başlangıçta boş
        trim_dd = gr.Dropdown(choices=[], label="Donanım (Trim)", interactive=True) # Başlangıçta boş

    with gr.Row():
        mileage_num = gr.Number(label="Kilometre", minimum=200, maximum=600000, step=1000, value=50000)
        type_dd = gr.Dropdown(choices=[], label="Araç Tipi", interactive=True) # Başlangıçta boş
        cylinder_dd = gr.Dropdown(choices=cylinder_options, label="Silindir", interactive=True)

    with gr.Row():
        liter_num = gr.Number(label="Motor Hacmi (Litre)", minimum=0.8, maximum=8.0, step=0.1, value=2.0)
        doors_dd = gr.Dropdown(choices=doors_options, label="Kapı Sayısı", interactive=True)
        cruise_rb = gr.Radio(choices=[True, False], label="Hız Sabitleme", value=True, type="value")

    with gr.Row():
        sound_rb = gr.Radio(choices=[True, False], label="Gelişmiş Ses Sistemi", value=True, type="value")
        leather_rb = gr.Radio(choices=[True, False], label="Deri Koltuk", value=False, type="value")

    # Dinamik dropdown güncellemeleri için olay dinleyicileri
    make_dd.change(fn=update_models, inputs=make_dd, outputs=model_dd)
    make_dd.change(fn=lambda: (gr.Dropdown(choices=[], value=None), gr.Dropdown(choices=[], value=None)), outputs=[trim_dd, type_dd]) # Marka değişince trim ve type sıfırla

    model_dd.change(fn=update_trims, inputs=[make_dd, model_dd], outputs=trim_dd)
    model_dd.change(fn=lambda: gr.Dropdown(choices=[], value=None), outputs=type_dd) # Model değişince type sıfırla

    trim_dd.change(fn=update_types, inputs=[make_dd, model_dd, trim_dd], outputs=type_dd)

    predict_button = gr.Button("Fiyat Tahmini Yap 💰")
    output_text = gr.Textbox(label="Tahmini Sonuç")

    predict_button.click(
        fn=predict_price,
        inputs=[make_dd, model_dd, trim_dd, mileage_num, type_dd, cylinder_dd, liter_num, doors_dd, cruise_rb, sound_rb, leather_rb],
        outputs=output_text
    )

    gr.Markdown("---")
    gr.Markdown("### 💡 Kullanım Notları:")
    gr.Markdown("- Lütfen tüm alanları doğru bir şekilde doldurun.")
    gr.Markdown("- **Marka** seçimi, **Model** seçeneklerini günceller.")
    gr.Markdown("- **Model** seçimi, **Donanım (Trim)** seçeneklerini günceller.")
    gr.Markdown("- **Marka, Model ve Donanım** seçimi, **Araç Tipi** seçeneklerini günceller.")
    gr.Markdown("- 'Hız Sabitleme', 'Gelişmiş Ses Sistemi' ve 'Deri Koltuk' için 'True' (Var) veya 'False' (Yok) seçimi yapınız.")


if __name__ == '__main__':
    if pipe is None or df.empty:
        print("Model veya veri yüklenemediği için Gradio arayüzü başlatılamıyor.")
        print("Lütfen 'car_price_model.pkl' ve 'cars.xls' dosyalarının varlığını ve doğruluğunu kontrol edin.")
    else:
        demo.launch()