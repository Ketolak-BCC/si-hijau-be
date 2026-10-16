import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select

from app.core.database import AsyncSessionLocal, Base, engine
from app.core.security import get_password_hash
from app.models.guide import ProcessingGuide
from app.models.partner import Partner
from app.models.user import FreeTimeLevel, User, UserRole


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        admin_check = await session.execute(select(User).where(User.email == "admin@sihijau.id"))
        if not admin_check.scalars().first():
            admin_user = User(
                email="admin@sihijau.id",
                hashed_password=get_password_hash("admin123"),
                full_name="Admin SiHijau",
                role=UserRole.ADMIN,
                has_yard=True,
                free_time_level=FreeTimeLevel.HIGH,
            )
            session.add(admin_user)

        user_check = await session.execute(select(User).where(User.email == "raka@sihijau.id"))
        if not user_check.scalars().first():
            demo_user = User(
                email="raka@sihijau.id",
                hashed_password=get_password_hash("password123"),
                full_name="Raka Pratama",
                role=UserRole.USER,
                auth_provider="local",
                has_yard=False,
                free_time_level=FreeTimeLevel.LOW,
            )
            session.add(demo_user)

        google_check = await session.execute(select(User).where(User.email == "demo.google@sihijau.id"))
        if not google_check.scalars().first():
            google_user = User(
                email="demo.google@sihijau.id",
                hashed_password=None,
                full_name="Demo Google User",
                role=UserRole.USER,
                auth_provider="google",
                google_id="google-demo-1234567890",
                avatar_url="https://lh3.googleusercontent.com/a/default-avatar",
                has_yard=True,
                free_time_level=FreeTimeLevel.MEDIUM,
            )
            session.add(google_user)

        guide_check = await session.execute(select(ProcessingGuide))
        if not guide_check.scalars().first():
            guide1 = ProcessingGuide(
                waste_category="ORGANIC",
                title="Panduan Kompos Sederhana Metode Takakura / Ember Bertumpuk",
                summary="Metode pengomposan mandiri skala rumah tangga tanpa bau busuk, cocok untuk sisa sayur dan buah.",
                difficulty="EASY",
                estimated_time="15-20 menit per batch",
                steps=[
                    {
                        "step_number": 1,
                        "title": "Pilah & Cacah Sampah",
                        "instruction": "Pisahkan sisa sayur/buah dari bahan hewani/minyak, lalu potong kecil-kecil ukuran 2-3 cm.",
                    },
                    {
                        "step_number": 2,
                        "title": "Campurkan Material Kering (Cokelat)",
                        "instruction": "Masukkan ke dalam wadah kompos dengan perbandingan 1:1 antara sampah organik dan serbuk gergaji/daun kering.",
                    },
                    {
                        "step_number": 3,
                        "title": "Aduk dan Jaga Kelembapan",
                        "instruction": "Aduk 2 hari sekali untuk sirkulasi udara. Kompos akan matang dan siap pakai dalam 3-4 minggu.",
                    },
                ],
            )
            guide2 = ProcessingGuide(
                waste_category="PLASTIC",
                title="Panduan Pembuatan Ecobrick dari Plastik Kemasan Kering",
                summary="Solusi mengunci limbah plastik tak bernilai jual tinggi agar tidak mencemari lingkungan.",
                difficulty="MEDIUM",
                estimated_time="30 menit",
                steps=[
                    {
                        "step_number": 1,
                        "title": "Bersihkan & Keringkan",
                        "instruction": "Cuci bersih plastik pembungkus makanan ringan dan jemur hingga benar-benar kering.",
                    },
                    {
                        "step_number": 2,
                        "title": "Potong Menjadi Bagian Kecil",
                        "instruction": "Gunting plastik menjadi potongan kecil agar mudah dipadatkan.",
                    },
                    {
                        "step_number": 3,
                        "title": "Padatkan ke Botol Plastik",
                        "instruction": "Masukkan ke dalam botol PET 600ml menggunakan tongkat kayu hingga botol terasa sangat padat dan keras.",
                    },
                ],
            )
            session.add_all([guide1, guide2])

        partner_check = await session.execute(select(Partner))
        if not partner_check.scalars().first():
            partners = [
                Partner(
                    name="Bank Sampah Malang Pusat",
                    address="Jl. Supriadi No. 24, Sukun, Kota Malang, Jawa Timur",
                    latitude=-7.9826,
                    longitude=112.6308,
                    accepted_categories="PLASTIC,PAPER,METAL,GLASS",
                    phone_number="+6281234567890",
                    operational_hours="Senin - Sabtu (08:00 - 15:00 WIB)",
                    capacity_info="Kapasitas harian 500 Kg",
                    requirements="Sampah anorganik wajib dipilah sesuai jenis dan dalam kondisi bersih & kering.",
                    is_active=True,
                ),
                Partner(
                    name="Rumah Maggot BSF Lestari",
                    address="Jl. Raya Tlogomas No. 88, Lowokwaru, Kota Malang",
                    latitude=-7.9351,
                    longitude=112.6012,
                    accepted_categories="ORGANIC,FOOD_WASTE",
                    phone_number="+6285799887766",
                    operational_hours="Setiap Hari (07:00 - 17:00 WIB)",
                    capacity_info="Menerima hingga 100 Kg sisa makanan per hari",
                    requirements="Hanya menerima sisa makanan organik non-plastik. Bebas deterjen dan minyak berlebih.",
                    is_active=True,
                ),
                Partner(
                    name="TPS 3R Hijau Berseri",
                    address="Jl. Soekarno Hatta No. 45, Kota Malang",
                    latitude=-7.9467,
                    longitude=112.6159,
                    accepted_categories="ORGANIC,PLASTIC,PAPER,METAL,GLASS",
                    phone_number="+6281987654321",
                    operational_hours="Senin - Jumat (08:00 - 14:00 WIB)",
                    capacity_info="Menerima sampah terpilah rumah tangga",
                    requirements="Bawa wadah sendiri atau kantong terpilah.",
                    is_active=True,
                ),
            ]
            session.add_all(partners)

        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed())
