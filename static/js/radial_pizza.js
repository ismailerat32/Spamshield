const slices = document.querySelectorAll(".slice");
const panel = document.getElementById("infoPanel");
const panelBadge = document.getElementById("panelBadge");
const panelTitle = document.getElementById("panelTitle");
const panelDesc = document.getElementById("panelDesc");
const panelBody = document.getElementById("panelBody");

const data = {
    koruma: {
        icon: "🛡️",
        title: "Spam Koruma",
        desc: "Şüpheli mesajları filtreleme ve canlı koruma yönetimi.",
        items: [
            ["Canlı koruma", "Anlık SMS akışında riskli mesajları algılar."],
            ["Risk eşiği", "Spam puanı kaç olunca engelleneceğini belirler."],
            ["Anahtar kelime kalkanı", "Belirli kelimeleri doğrudan yakalar."]
        ]
    },
    analiz: {
        icon: "📩",
        title: "SMS Analizi",
        desc: "Mesajların içerik, link ve kelime bazlı analiz ekranı.",
        items: [
            ["Mesaj skoru", "Her SMS için spam güven puanı üretir."],
            ["Link denetimi", "Mesaj içindeki bağlantıları risk açısından işaretler."],
            ["Kelime tarama", "Spam kelime yoğunluğunu gösterir."]
        ]
    },
    engel: {
        icon: "🚫",
        title: "Engellenenler",
        desc: "Bloklanan numaralar ve kara liste yönetimi.",
        items: [
            ["Numara listesi", "Engellenen kaynakları görüntüler."],
            ["Tek dokunuş yönetim", "İstediğin numarayı kaldır veya tekrar ekle."],
            ["Kural geçmişi", "Neden engellendiğini gösterir."]
        ]
    },
    bildirim: {
        icon: "🔔",
        title: "Bildirimler",
        desc: "Kritik olaylar, uyarılar ve lisans hatırlatmaları.",
        items: [
            ["Tehdit uyarısı", "Şüpheli dalga tespit edildiğinde haber verir."],
            ["Lisans durumu", "Süre bitişine yakın hatırlatma yapar."],
            ["Sistem bildirimi", "Önemli uygulama olaylarını gösterir."]
        ]
    },
    topluluk: {
        icon: "👥",
        title: "Topluluk",
        desc: "Ortak spam raporları ve paylaşılan tehdit verileri.",
        items: [
            ["Ortak rapor", "Diğer kullanıcılardan gelen spam bilgisi."],
            ["Tehdit paylaşımı", "Yeni dolandırıcılık türlerini görürsün."],
            ["Güçlü havuz", "Topluluk verisiyle filtreyi besler."]
        ]
    },
    ayarlar: {
        icon: "⚙️",
        title: "Ayarlar",
        desc: "Tema, davranış ve kullanıcı tercihleri yönetimi.",
        items: [
            ["Tema seçimi", "Koyu veya premium görünüm ayarlanır."],
            ["Bildirim kontrolü", "Hangi uyarıların geleceği seçilir."],
            ["Genel tercihler", "Uygulamanın çalışma biçimi özelleştirilir."]
        ]
    }
};

function renderPanel(key) {
    const item = data[key];
    if (!item) return;

    panelBadge.textContent = item.icon;
    panelTitle.textContent = item.title;
    panelDesc.textContent = item.desc;

    panelBody.innerHTML = item.items.map(([title, desc]) => `
        <div class="item-card">
            <strong>${title}</strong>
            <div>${desc}</div>
        </div>
    `).join("");

    panel.classList.add("active");
}

slices.forEach((slice) => {
    slice.addEventListener("click", () => {
        slices.forEach((s) => s.classList.remove("active"));
        slice.classList.add("active");
        renderPanel(slice.dataset.key);
    });
});
