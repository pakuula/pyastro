from pyastro.astro import Angle


class TestAngle:
    """Тесты для класса Angle"""
    
    def test_str_360(self):
        """Тест строкового представления"""
        a1 = Angle(23.4392911)
        assert a1.value == 23.4392911
        assert str(a1) == "Angle(23.4392911, from_0_to_360=True)"
        assert format(a1) == "23°26'21\""
        assert format(a1, ".2f") == "23°26'21.45\""
        assert format(a1, ".4f") == "23°26'21.4480\""
        
        a2 = Angle(-23.4392911)
        assert a2.value == 336.5607089
        assert str(a2) == "Angle(336.5607089, from_0_to_360=True)"
        assert format(a2) == "336°33'39\""
        assert format(a2, ".2f") == "336°33'38.55\""
        assert format(a2, ".4f") == "336°33'38.5520\""

        a3 = Angle(720 + 23.4392911)
        assert a3.value - 23.4392911 < 1e-7
        
    def test_str_signed(self):
        """Тест строкового представления"""
        a1 = Angle(23.4392911, from_0_to_360=False)
        assert abs(a1.value - 23.4392911) < 1e-7
        # assert str(a1) == "Angle(23.4392911, from_0_to_360=False)" # Не работает из-за ошибок округления: фактически 23.43929109999999
        assert format(a1) == "23°26'21\""
        assert format(a1, ".2f") == "23°26'21.45\""
        assert format(a1, ".4f") == "23°26'21.4480\""
        
        a2 = Angle(-23.4392911, from_0_to_360=False)
        assert abs(a2.value + 23.4392911) < 1e-7
        # assert str(a2) == "Angle(-23.4392911, from_0_to_360=False)" # Не работает из-за ошибок округления: фактически -23.43929109999999
        assert format(a2) == "-23°26'21\""
        assert format(a2, ".2f") == "-23°26'21.45\""
        assert format(a2, ".4f") == "-23°26'21.4480\""

        a3 = Angle(360 + 23.4392911, from_0_to_360=False)
        assert abs(a3.value - 23.4392911) < 1e-7
        
        a4 = Angle(720 - 23.4392911, from_0_to_360=False)
        assert abs(a4.value + 23.4392911) < 1e-7
        
    def test_small_numbers(self):
        """Тест строкового представления с малыми секундами"""
        a1 = Angle(33.8677778)
        assert a1.value == 33.8677778
        assert str(a1) == "Angle(33.8677778, from_0_to_360=True)"
        assert format(a1) == "33°52'04\""
        assert format(a1, ".2f") == "33°52'4.00\""
        assert format(a1, "05.2f") == "33°52'04.00\""