import json
import logging
import re
from dataclasses import dataclass, field

from google import genai
from google.genai import types

from app.core.config import settings
from app.models.waste import WasteCategoryEnum

logger = logging.getLogger(__name__)


@dataclass
class VisionResult:
    item_name: str
    category: WasteCategoryEnum
    confidence_score: float
    raw_analysis: str
    estimated_size: str | None = None
    physical_condition: str | None = None
    material_type: str | None = None
    item_specific_actions: list[str] = field(default_factory=list)


class VisionService:
    @staticmethod
    def _get_client() -> genai.Client | None:
        if settings.GEMINI_API_KEY:
            return genai.Client(api_key=settings.GEMINI_API_KEY)
        return None

    async def analyze_waste_image(
        self, image_bytes: bytes, mime_type: str = "image/jpeg"
    ) -> VisionResult:
        client = self._get_client()
        if not client:
            logger.info("GEMINI_API_KEY not configured. Using mock vision response.")
            mock_actions = [
                "1. Pot Tanaman Gantung Vertikal / Hidroponik Wick System: Karena botol berukuran besar 1.5L, potong 2 bagian untuk menampung media tanam dan air nutrisi secara memadai.",
                "2. Corong Tuang Minyak & Dispenser Pakan Hewan: Potong sepertiga atas menjadi corong penuang serbaguna atau dispenser pakan otomatis.",
                "3. Setorkan ke Bank Sampah Mitra SiHijau: Lepas tutup dan label plastik, pipihkan botol PET bening 1.5L untuk disetor dengan nilai jual daur ulang tinggi."
            ]
            return VisionResult(
                item_name="Botol Air Mineral Plastik Bekas 1.5L",
                category=WasteCategoryEnum.PLASTIC,
                confidence_score=0.95,
                raw_analysis=json.dumps({
                    "description": "Model mock: Botol plastik PET 1.5L terdeteksi dalam kondisi bersih dan utuh.",
                    "estimated_size": "1.5 Liter (Besar)",
                    "physical_condition": "Utuh dan bersih",
                    "material_type": "Plastik PET (Kode 1)",
                    "item_specific_actions": mock_actions
                }, ensure_ascii=False),
                estimated_size="1.5 Liter (Besar)",
                physical_condition="Utuh dan bersih",
                material_type="Plastik PET (Kode 1)",
                item_specific_actions=mock_actions,
            )

        prompt = """
        Anda adalah Asisten AI Pakar Pemilahan Sampah & Daur Ulang untuk platform lingkungan "SiHijau".
        Tugas utama Anda adalah mengidentifikasi OBJEK KEMASAN / BARANG BEKAS / SISA KONSUMSI / LIMBAH FISIK di dalam gambar dan menentukan jenis material serta panduan pengolahannya.

        ======================================================================
        ATURAN UTAMA & PENANGANAN EDGE CASES (BACA DENGAN SANGAT TELITI!):
        ======================================================================

        1. EDGE CASE: MANUSIA / TANGAN SEDANG MEMEGANG OBJEK (FOTO SELFIE / KAMERA DEPAN)
           - Pengguna aplikasi mobile SANGAT SERING mengambil foto atau berswafoto (selfie) sambil MEMEGANG objek sampah/kemasan (contoh: memegang cup kopi plastik, cup boba, botol air, kaleng soda, bungkus snack, kotak take-away, baterai bekas, dll).
           - ATURAN MUTLAK: JANGAN PERNAH mengklasifikasikan gambar sebagai "NOT_WASTE" hanya karena terlihat wajah, tubuh, atau tangan orang di foto!
           - FOKUS ANALISIS HARUS DITUJUKAN PADA OBJEK KEMASAN / BARANG BEKAS YANG SEDANG DIPEGANG ATAU DIARAHKAN KE KAMERA, BUKAN ORANGNYA!
           - Contoh: Foto selfie seseorang memegang cup plastik kopi/es boba (seperti cup bertuliskan Teka/Janji Jiwa/Kopi Kenangan) -> OBJEK TARGET ADALAH CUP TERSEBUT! Kategori: "PLASTIC", item_name: "Gelas / Cup Plastik Minuman (PP/PET) dengan Sedotan".

        2. EDGE CASE: KEMASAN MASIH BERISI SISA MINUMAN / ES BATU / SEDOTAN PLASTIK
           - Cup, botol, atau wadah yang masih ada sisa cairan, es batu, sedotan, atau baru selesai diminum TETAP MERUPAKAN SAMPAH KEMASAN KONSUMSI yang perlu dipilah (Kategori: "PLASTIC", "PAPER", dll).
           - JANGAN dianggap sebagai "konsumsi aktif non-sampah". Kemasan sekali pakai selalu menjadi limbah yang memerlukan pembuangan atau daur ulang!
           - Berikan instruksi realistis di poin aksi (misal: habiskan/buang es batu, bilas sisa minuman, pisahkan sedotan dari badan cup).

        3. EDGE CASE: LATAR BELAKANG RUANGAN / KAFE / MEJA KERJA / OUTDOOR
           - Abaikan latar belakang ruangan, meja kafe, kursi, mobil, atau dinding. Fokus pada objek buangan/kemasan di bagian depan (foreground).

        4. EDGE CASE: KEMASAN PENYOK / REMUK / SOBEK / DILIPAT
           - Botol plastik yang diremas gepeng, kardus yang dilipat/penyok, kaleng penyok, atau kemasan sobek tetap diidentifikasi sesuai material aslinya.

        5. KAPAN STATUS "NOT_WASTE" BOLEH DIGUNAKAN? (HANYA JIKA MEMENUHI SALAH SATU DI BAWAH INI):
           - Kategori "NOT_WASTE" HANYA boleh dipilih jika:
             a. Gambar murni desain grafis digital 2D, logo perusahaan, ilustrasi vektor, icon, atau tangkapan layar (screenshot) layar monitor/HP tanpa ada objek fisik di dunia nyata.
             b. Foto manusia, wajah, hewan, atau pemandangan yang SAMA SEKALI TIDAK MEMEGANG / MENAMPILKAN objek kemasan, makanan sisa, atau barang buangan apapun (misal: hanya foto selfie wajah close-up tanpa barang di tangan).
             c. Objek berharga/perabot utuh yang jelas bukan sampah dan tidak sedang dipegang sebagai buangan (misal: laptop menyala di meja kerja, mobil yang sedang melaju di jalan).
           - JIKA ADA OBJEK KEMASAN/BARANG BEKAS YANG DIPEGANG ATAU DITAMPILKAN -> OTOMATIS BUKAN NOT_WASTE!

        ======================================================================
        PANDUAN KATEGORI MATERIAL (PILIH SALAH SATU YANG PALING SESUAI):
        ======================================================================
        - "PLASTIC"    : Cup minuman plastik (kopi, boba, pop ice, jus), botol plastik (Aqua, Le Minerale), sedotan plastik, kantong kresek, bungkus sachet makanan ringan, wadah mika, styrofoam, jeriken.
        - "PAPER"      : Paper cup (gelas kertas kopi panas), kardus packing, karton makanan (kotak bekal/nasi kotak), kertas HVS, kantong kertas (paper bag), koran.
        - "METAL"      : Kaleng minuman bersoda/larutan/susu, kaleng biskuit, tutup botol logam, seng, kawat.
        - "GLASS"      : Botol kaca sirup/bir/kecap, toples kaca selai, pecahan kaca/beling.
        - "ORGANIC"    : Sisa dedaunan, ranting, bunga gugur, kulit buah mentah (pisang, jeruk), ampas sayuran, sisa tanaman.
        - "FOOD_WASTE" : Sisa makanan olahan, nasi sisa/basi, sisa masakan, tulang ayam/ikan, ampas makanan berminyak.
        - "EWASTE"     : Baterai bekas, charger rusak, kabel charger/headset putus, bohlam/lampu, komponen elektronik.
        - "HAZARDOUS"  : Kemasan obat kadaluarsa, botol pestisida/cairan pembersih lantai kimia keras, aerosol/kaleng semprot.
        - "NOT_WASTE"  : HANYA jika memenuhi aturan pengecualian ketat poin 5.

        ======================================================================
        OUTPUT FORMAT (JSON VALID SAJA, TANPA TANDA MARKDOWN):
        ======================================================================
        {
          "is_waste": true,
          "category": "PLASTIC",
          "item_name": "Cup Plastik Minuman Bekas (Teka/Kopi/Boba) dengan Sedotan",
          "confidence_score": 0.95,
          "estimated_size": "Sedang (Gelas 16-22 oz)",
          "physical_condition": "Bekas konsumsi, terdapat sedotan plastik dan sisa cairan",
          "material_type": "Plastik PP (Polypropylene) / PET",
          "description": "Gelas kemasan minuman plastik sekali pakai yang sedang dipegang oleh pengguna. Terdapat sedotan dan sisa cairan es di dalamnya.",
          "item_specific_actions": [
            "1. Pengosongan & Pembersihan: Buang sisa es batu dan cairan minuman ke wastafel. Bilas bagian dalam gelas dengan sedikit air agar bersih dari sisa gula dan tidak mengundang serangga.",
            "2. Pemilahan Sedotan & Tutup Seal: Pisahkan sedotan plastik dan lapisan tutup plastik seal dari badan gelas (karena sedotan biasanya berbahan plastik berbeda dari cup).",
            "3. Penyaluran Daur Ulang: Keringkan dan tumpuk gelas plastik PP bening agar ringkas, lalu setorkan ke drop-box anorganik atau bank sampah mitra SiHijau (plastik cup bening memiliki nilai jual daur ulang tinggi)."
          ]
        }
        """

        candidate_models = [
            "gemini-3.1-flash-lite",
            "gemini-3.1-flash-lite-preview",
            "gemini-flash-lite-latest",
        ]

        last_error = None
        for model in candidate_models:
            try:
                logger.info(f"Invoking Gemini model: {model}...")
                response = client.models.generate_content(
                    model=model,
                    contents=[
                        types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                        prompt,
                    ],
                )
                text_response = response.text.strip()
                logger.info(f"Gemini Vision raw response ({model}): {text_response}")

                match = re.search(r"\{.*\}", text_response, re.DOTALL)
                if match:
                    clean_json = match.group(0)
                else:
                    clean_json = text_response.strip("`").replace("json\n", "", 1).strip()

                data = json.loads(clean_json)
                is_waste = data.get("is_waste", True)
                raw_category = str(data.get("category", "")).upper()

                if not is_waste or raw_category == "NOT_WASTE":
                    category = WasteCategoryEnum.NOT_WASTE
                    confidence = float(data.get("confidence_score", 0.0))
                else:
                    try:
                        category = WasteCategoryEnum(raw_category)
                    except ValueError:
                        category = WasteCategoryEnum.PLASTIC
                    confidence = float(data.get("confidence_score", 0.85))

                item_specific_actions = data.get("item_specific_actions", [])
                if not isinstance(item_specific_actions, list):
                    item_specific_actions = []

                # Format raw analysis as structured JSON string so it stores cleanly in DB Text column
                structured_raw = json.dumps({
                    "description": data.get("description", ""),
                    "estimated_size": data.get("estimated_size", "Sedang"),
                    "physical_condition": data.get("physical_condition", "Utuh"),
                    "material_type": data.get("material_type", ""),
                    "item_specific_actions": item_specific_actions
                }, ensure_ascii=False)

                return VisionResult(
                    item_name=data.get("item_name", "Sampah Terdeteksi"),
                    category=category,
                    confidence_score=confidence,
                    raw_analysis=structured_raw,
                    estimated_size=data.get("estimated_size"),
                    physical_condition=data.get("physical_condition"),
                    material_type=data.get("material_type"),
                    item_specific_actions=item_specific_actions,
                )
            except Exception as e:
                logger.warning(f"Model {model} failed ({e}). Cascading to next candidate...")
                last_error = e
                continue

        logger.error(f"All Gemini Vision models failed. Last error: {last_error}", exc_info=True)
        return VisionResult(
            item_name="Pemindaian Tertunda (Layanan Sibuk)",
            category=WasteCategoryEnum.NOT_WASTE,
            confidence_score=0.0,
            raw_analysis=json.dumps({
                "description": "Layanan AI sedang mengalami lonjakan antrean trafik tinggi. Silakan ulangi pemindaian beberapa saat lagi.",
                "estimated_size": "N/A",
                "physical_condition": "N/A",
                "material_type": "N/A",
                "item_specific_actions": []
            }, ensure_ascii=False),
        )


vision_service = VisionService()
