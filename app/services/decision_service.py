from app.models.user import FreeTimeLevel
from app.models.waste import ActionTypeEnum, DifficultyEnum, WasteCategoryEnum
from app.schemas.decision import DecisionOption, DecisionResponse


class DecisionEngine:
    @staticmethod
    def evaluate(
        waste_category: WasteCategoryEnum,
        item_name: str,
        has_yard: bool,
        free_time_level: FreeTimeLevel,
        estimated_size: str | None = None,
        item_specific_actions: list[str] | None = None,
    ) -> DecisionResponse:
        recommendations: list[DecisionOption] = []
        user_context = {
            "has_yard": has_yard,
            "free_time_level": free_time_level.value,
            "estimated_size": estimated_size or "Tidak Ditentukan",
        }

        action_points: list[str] = []
        feasibility_notes: str | None = None

        item_lower = (item_name or "").lower()
        size_lower = (estimated_size or "").lower()

        is_large_bottle = any(w in item_lower or w in size_lower for w in ["1.5", "1,5", "1.5l", "1500", "1l", "1000", "besar", "galon", "2l"])
        is_small_bottle = any(w in item_lower or w in size_lower for w in ["300", "330", "250", "240", "mini", "kecil", "gelas", "cup"])

        # 1. IF AI SPECIFIC ACTIONS WERE SUPPLIED FROM PHOTO SCAN
        if item_specific_actions and len(item_specific_actions) > 0:
            action_points = item_specific_actions
            if is_large_bottle and "botol" in item_lower:
                feasibility_notes = "Kapasitas 1.5L memiliki volume media tanam (~1200ml) yang mencukupi untuk perakaran tanaman sayur/herba (Pot Hidroponik Wick layak secara fisik)."
            elif is_small_bottle and "botol" in item_lower:
                feasibility_notes = "Ukuran mini 300ml-330ml TIDAK LAYAK untuk pot tanaman karena volume media tanah terlalu sempit dan akar akan mudah membusuk. Dialihkan untuk organizer meja atau daur ulang."

            primary_action = ActionTypeEnum.REUSE if ("pot" in str(action_points).lower() or "wadah" in str(action_points).lower()) else ActionTypeEnum.ALLOCATE

            for idx, pt in enumerate(action_points):
                clean_pt = pt.lstrip("0123456789. ")
                title_part = clean_pt.split(":")[0] if ":" in clean_pt else f"Opsi Solusi {idx+1}"
                desc_part = clean_pt.split(":", 1)[1].strip() if ":" in clean_pt else clean_pt

                act_type = ActionTypeEnum.REUSE if idx == 0 else (ActionTypeEnum.PROCESS_MYSELF if idx == 1 else ActionTypeEnum.ALLOCATE)
                recommendations.append(
                    DecisionOption(
                        action_type=act_type,
                        title=title_part,
                        description=desc_part,
                        difficulty=DifficultyEnum.EASY if idx == 0 else DifficultyEnum.MEDIUM,
                        estimated_time="5-15 menit",
                        is_primary_recommendation=(idx == 0),
                    )
                )

            return DecisionResponse(
                waste_category=waste_category,
                item_name=item_name,
                user_context=user_context,
                primary_action=primary_action,
                recommendations=recommendations,
                item_specific_action_points=action_points,
                physical_feasibility_notes=feasibility_notes,
            )

        # 2. RULE-BASED AND PHYSICAL ATTRIBUTE INFERENCE
        if waste_category in [WasteCategoryEnum.ORGANIC, WasteCategoryEnum.FOOD_WASTE]:
            if has_yard and free_time_level in [FreeTimeLevel.MEDIUM, FreeTimeLevel.HIGH]:
                primary_action = ActionTypeEnum.PROCESS_MYSELF
                feasibility_notes = "Pekarangan rumah memadai untuk sirkulasi oksigen komposting aerob/biopori tanpa mengganggu ruangan dalam rumah."
                action_points = [
                    "1. Kompos Takakura / Lubang Biopori Mandiri: Cacah sisa organik menjadi potongan kecil 1-2 cm agar cepat terdekomposisi dalam 2-3 minggu.",
                    "2. Pupuk Organik Cair (POC) / Eco-Enzyme: Rendam sisa kulit buah mentah manis dengan air dan molase gula merah dalam wadah tertutup.",
                    "3. Salurkan ke Peternak / Budidaya Maggot BSF: Jika volume sisa makanan terlalu banyak, serahkan ke pengolah maggot mitra SiHijau terdekat."
                ]
                recommendations.append(
                    DecisionOption(
                        action_type=ActionTypeEnum.PROCESS_MYSELF,
                        title="Pembuatan Kompos Mandiri / Biopori Pekarangan",
                        description="Karena Anda memiliki pekarangan dan waktu luang, mengolah sisa organik menjadi pupuk kompos atau biopori adalah pilihan paling efisien.",
                        difficulty=DifficultyEnum.EASY,
                        estimated_time="15-30 menit",
                        is_primary_recommendation=True,
                    )
                )
                recommendations.append(
                    DecisionOption(
                        action_type=ActionTypeEnum.ALLOCATE,
                        title="Salurkan ke Komunitas Budidaya Maggot / TPS 3R",
                        description="Jika tidak ingin mengompos sendiri, salurkan sisa makanan segar ke mitra pengolah maggot BSF terdekat.",
                        difficulty=DifficultyEnum.EASY,
                        estimated_time="10 menit",
                        is_primary_recommendation=False,
                    )
                )
            else:
                primary_action = ActionTypeEnum.ALLOCATE
                feasibility_notes = "Keterbatasan lahan atau waktu membuat pengomposan mandiri berisiko membusuk dan menimbulkan bau di ruangan tertutup."
                action_points = [
                    "1. Salurkan ke TPS 3R / Bank Sampah Organik Mitra: Kumpulkan dalam kantong terpisah dari anorganik dan serahkan ke drop-point terdekat.",
                    "2. Eco-Enzyme Wadah Tertutup Mini: Manfaatkan kulit buah manis di dalam botol tertutup tanpa butuh pekarangan luas.",
                    "3. Pisahkan dari Limbah Kering: Pastikan limbah organik tidak mengontaminasi kertas atau plastik yang dapat didaur ulang."
                ]
                recommendations.append(
                    DecisionOption(
                        action_type=ActionTypeEnum.ALLOCATE,
                        title="Salurkan ke Bank Sampah Organik / TPS 3R",
                        description="Karena keterbatasan lahan atau waktu, menyalurkan limbah organik ke mitra penerima adalah solusi paling praktis dan tepat.",
                        difficulty=DifficultyEnum.EASY,
                        estimated_time="10 menit",
                        is_primary_recommendation=True,
                    )
                )

        elif waste_category == WasteCategoryEnum.PLASTIC:
            if "botol" in item_lower or "wadah" in item_lower:
                if is_large_bottle:
                    primary_action = ActionTypeEnum.REUSE
                    feasibility_notes = "Botol berkapasitas besar (1.5L) memiliki volume media tanam ~1200ml yang mencukupi untuk ruang tumbuh akar sayuran seperti pakcoy, selada, atau mint (SANGAT COCOK untuk Pot Hidroponik Wick System)."
                    action_points = [
                        "1. Pot Tanaman Hidroponik Sumbu (Wick System): Potong botol 1.5L menjadi 2 bagian. Balikkan bagian corong atas ke bawah dengan sumbu kain flanel untuk kapilaritas nutrisi air dari wadah bawah.",
                        "2. Corong Tuang Dapur & Dispenser Pakan Hewan: Potong sepertiga atas kerucut untuk corong penuang beras/minyak atau dispenser makanan hewan otomatis.",
                        "3. Setorkan ke Bank Sampah Mitra SiHijau: Lepaskan tutup HDPE dan label plastik, pipihkan botol PET bening 1.5L untuk disetor dengan nilai jual daur ulang tinggi."
                    ]
                    recommendations.append(
                        DecisionOption(
                            action_type=ActionTypeEnum.REUSE,
                            title="Pot Tanaman Hidroponik Wick System (Kapasitas 1.5L Sesuai Foto)",
                            description="Karena volume botol 1.5L luas, botol ini ideal dibuat pot tanaman sayur/herba dengan sistem sumbu kain flanel mandiri.",
                            difficulty=DifficultyEnum.EASY,
                            estimated_time="15 menit",
                            is_primary_recommendation=True,
                        )
                    )
                    recommendations.append(
                        DecisionOption(
                            action_type=ActionTypeEnum.ALLOCATE,
                            title="Pipihkan & Setor ke Bank Sampah Mitra SiHijau",
                            description="Plastik PET bening berukuran 1.5L memiliki nilai ekonomis tinggi per kg di bank sampah daur ulang.",
                            difficulty=DifficultyEnum.EASY,
                            estimated_time="10 menit",
                            is_primary_recommendation=False,
                        )
                    )
                elif is_small_bottle:
                    primary_action = ActionTypeEnum.REUSE
                    feasibility_notes = "Botol ukuran mini (300ml - 330ml) memiliki volume terlalu sempit (<300ml) untuk pot tanaman. Media tanah yang terlalu sedikit membuat akar tanaman cepat membusuk atau tercekik. Sangat direkomendasikan dialihkan untuk wadah pernak-pernik atau disetor ke drop-box daur ulang."
                    action_points = [
                        "1. Wadah Organizer Klip & Pernak-Pernik Meja: Potong sepertiga atas botol 300ml, rapikan tepiannya untuk wadah koin, paper clip, peniti, atau jarum meja.",
                        "2. Wadah Travel Portabel Sabun Cair: Bersihkan dan keringkan untuk wadah isi ulang sabun cuci tangan darurat saat bepergian.",
                        "3. Pipihkan & Masukkan ke Drop-Box Daur Ulang: Pisahkan tutup botol, remas hingga gepeng, lalu setorkan ke bank sampah mitra SiHijau."
                    ]
                    recommendations.append(
                        DecisionOption(
                            action_type=ActionTypeEnum.REUSE,
                            title="Wadah Organizer Meja (Bukan untuk Pot Tanaman Karena Volume Sempit)",
                            description="Ukuran 300ml tidak cocok untuk pot tanaman karena media tanam terlalu sempit. Manfaatkan sebagai wadah klip/koin atau wadah stationary.",
                            difficulty=DifficultyEnum.EASY,
                            estimated_time="5 menit",
                            is_primary_recommendation=True,
                        )
                    )
                    recommendations.append(
                        DecisionOption(
                            action_type=ActionTypeEnum.ALLOCATE,
                            title="Pipihkan & Salurkan ke Drop-Box Bank Sampah",
                            description="Pisahkan tutup dan label, remas hingga gepeng untuk menghemat volume di drop-box daur ulang SiHijau.",
                            difficulty=DifficultyEnum.EASY,
                            estimated_time="5 menit",
                            is_primary_recommendation=False,
                        )
                    )
                else:
                    primary_action = ActionTypeEnum.REUSE
                    feasibility_notes = "Botol ukuran sedang (600ml) dapat dijadikan pot pembibitan awal atau wadah ecobrick."
                    action_points = [
                        "1. Pot Pembibitan Tunas Awal / Ecobrick: Cocok untuk persemaian bibit cabai atau wadah padat ecobrick.",
                        "2. Wadah Penyimpanan Alat Tulis Meja: Potong bagian atas dan manfaatkan tabung bawah.",
                        "3. Salurkan ke Bank Sampah Mitra: Cuci bersih, lepas label, dan setorkan ke pengepul mitra."
                    ]
                    recommendations.append(
                        DecisionOption(
                            action_type=ActionTypeEnum.REUSE,
                            title="Gunakan Kembali Sebagai Wadah / Pot Semai Mini",
                            description="Cuci bersih dan manfaatkan kembali untuk pot semai bibit tanaman atau wadah penyimpanan.",
                            difficulty=DifficultyEnum.EASY,
                            estimated_time="5 menit",
                            is_primary_recommendation=True,
                        )
                    )
                    recommendations.append(
                        DecisionOption(
                            action_type=ActionTypeEnum.ALLOCATE,
                            title="Salurkan ke Bank Sampah / Pengepul Daur Ulang",
                            description="Kumpulkan hingga jumlah tertentu, pipihkan, dan setorkan ke mitra penerima sampah anorganik.",
                            difficulty=DifficultyEnum.EASY,
                            estimated_time="10 menit",
                            is_primary_recommendation=False,
                        )
                    )
            else:
                primary_action = ActionTypeEnum.ALLOCATE
                feasibility_notes = "Kemasan plastik kresek/sachet memiliki fleksibilitas tinggi dan cocok untuk kantong sampah sekunder atau ecobrick."
                action_points = [
                    "1. Gunakan Kembali Sebagai Kantong Sampah Kering Rumah Tangga: Alihkan untuk wadah limbah kering.",
                    "2. Cuci Bersih & Buat Ecobrick: Gunting kecil-kecil dan padatkan ke dalam botol plastik bekas.",
                    "3. Kumpulkan & Salurkan ke Bank Sampah Daur Ulang Plastik Lembaran."
                ]
                recommendations.append(
                    DecisionOption(
                        action_type=ActionTypeEnum.ALLOCATE,
                        title="Salurkan ke Bank Sampah Terdekat",
                        description="Kumpulkan dan serahkan ke unit bank sampah terdekat untuk didaur ulang secara industri.",
                        difficulty=DifficultyEnum.EASY,
                        estimated_time="10 menit",
                        is_primary_recommendation=True,
                    )
                )

        elif waste_category in [WasteCategoryEnum.PAPER, WasteCategoryEnum.GLASS, WasteCategoryEnum.METAL]:
            primary_action = ActionTypeEnum.ALLOCATE
            feasibility_notes = f"Material {waste_category.value} memiliki siklus daur ulang tertutup (closed-loop) industri dengan nilai ekonomi tinggi."
            action_points = [
                f"1. Pilah Bersih Kategori {waste_category.value}: Pisahkan dari kotoran basah, minyak, dan lakban perekat.",
                "2. Gunakan Ulang Kemasan Utuh: Manfaatkan kardus utuh untuk kotak simpan atau toples kaca untuk wadah bumbu.",
                "3. Setor ke Bank Sampah / Pengepul Mitra SiHijau untuk Ditimbang dan Ditukar Poin."
            ]
            recommendations.append(
                DecisionOption(
                    action_type=ActionTypeEnum.ALLOCATE,
                    title="Pilah & Salurkan ke Bank Sampah Bernilai Ekonomis",
                    description=f"Limbah kategori {waste_category.value} memiliki nilai daur ulang tinggi di bank sampah atau pengepul mitra.",
                    difficulty=DifficultyEnum.EASY,
                    estimated_time="10 menit",
                    is_primary_recommendation=True,
                )
            )

        elif waste_category == WasteCategoryEnum.NOT_WASTE:
            primary_action = ActionTypeEnum.REUSE
            feasibility_notes = "Bukan merupakan sampah fisik."
            action_points = [
                "1. Objek Terdeteksi Bukan Sampah Fisik: Tidak memerlukan tindakan pembuangan atau daur ulang.",
                "2. Simpan atau Gunakan Sesuai Fungsi Aslinya.",
                "3. Scan Kembali Objek Sampah Nyata untuk Mendapatkan Analisis Pengolahan."
            ]
            recommendations.append(
                DecisionOption(
                    action_type=ActionTypeEnum.REUSE,
                    title="Bukan Sampah Fisik / Tidak Perlu Dibuang",
                    description="Objek yang terdeteksi bukan merupakan sampah fisik yang memerlukan pembuangan atau daur ulang.",
                    difficulty=DifficultyEnum.EASY,
                    estimated_time="0 menit",
                    is_primary_recommendation=True,
                )
            )

        else:
            primary_action = ActionTypeEnum.ALLOCATE
            feasibility_notes = "Penanganan limbah khusus/berbahaya membutuhkan fasilitas pengolahan tersertifikasi."
            action_points = [
                "1. Pisahkan dan Simpan di Tempat Kering Tertutup: Jangan dicampur dengan sampah harian.",
                "2. Serahkan ke Dropbox B3 / E-Waste Resmi Dinas Lingkungan Hidup / Mitra SiHijau.",
                "3. Jangan Dibakar atau Dibuang Sembarangan untuk Mencegah Pencemaran Tanah dan Air."
            ]
            recommendations.append(
                DecisionOption(
                    action_type=ActionTypeEnum.ALLOCATE,
                    title="Salurkan ke Fasilitas Pengolahan Limbah Khusus Terdekat",
                    description="Serahkan limbah ke fasilitas pengelolaan sampah terdekat.",
                    difficulty=DifficultyEnum.EASY,
                    estimated_time="10 menit",
                    is_primary_recommendation=True,
                )
            )

        return DecisionResponse(
            waste_category=waste_category,
            item_name=item_name,
            user_context=user_context,
            primary_action=primary_action,
            recommendations=recommendations,
            item_specific_action_points=action_points,
            physical_feasibility_notes=feasibility_notes,
        )


decision_engine = DecisionEngine()
