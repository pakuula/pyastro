import pytest
from pyastro.util import parse_lat, parse_lon, CoordError


class TestParseLat:
    """Тесты для функции parse_lat"""
    
    def test_parse_lat_decimal_degrees(self):
        """Тест парсинга широты в десятичных градусах"""
        assert parse_lat("56.25") == 56.25
        assert parse_lat("-45.0") == -45.0
        assert parse_lat("0.0") == 0.0
        assert parse_lat("90") == 90.0
        assert parse_lat("-90") == -90.0
    
    def test_parse_lat_with_hemisphere_letters(self):
        """Тест парсинга широты с буквами полушария"""
        assert parse_lat("56.25N") == 56.25
        assert parse_lat("56.25 N") == 56.25
        assert parse_lat("56.25S") == -56.25
        assert parse_lat("56.25 S") == -56.25
        assert parse_lat("n56.25") == 56.25
        assert parse_lat("s56.25") == -56.25
    
    def test_parse_lat_degrees_minutes(self):
        """Тест парсинга широты в градусах и минутах"""
        assert parse_lat("56 15") == 56.25  # 56°15' = 56 + 15/60
        assert parse_lat("56°15′") == 56.25
        assert parse_lat("56:15") == 56.25
        assert parse_lat("56 15 N") == 56.25
        assert parse_lat("56 15 S") == -56.25
        assert parse_lat("-56 15") == -56.25
    
    def test_parse_lat_degrees_minutes_seconds(self):
        """Тест парсинга широты в градусах, минутах и секундах"""
        assert parse_lat("56 15 30") == 56.25833333333333  # 56°15'30" = 56 + 15/60 + 30/3600
        assert parse_lat("56°15′30″") == 56.25833333333333
        assert parse_lat("56:15:30") == 56.25833333333333
        assert parse_lat("56 15 30 N") == 56.25833333333333
        assert parse_lat("56 15 30 S") == -56.25833333333333
        assert parse_lat("-56 15 30") == -56.25833333333333
    
    def test_parse_lat_mixed_formats(self):
        """Тест различных смешанных форматов"""
        assert parse_lat("56n15.5") == 56.25833333333333  # 56°15.5' = 56 + 15.5/60
        assert parse_lat("37e30") == 37.5  # E/W для широты должно работать как N/S
        assert parse_lat("56 15.5") == 56.25833333333333
    
    def test_parse_lat_boundary_values(self):
        """Тест граничных значений широты"""
        assert parse_lat("90") == 90.0
        assert parse_lat("-90") == -90.0
        assert parse_lat("90 N") == 90.0
        assert parse_lat("90 S") == -90.0
        assert parse_lat("0") == 0.0
    
    def test_parse_lat_whitespace_handling(self):
        """Тест обработки пробелов"""
        assert parse_lat("  56.25  ") == 56.25
        assert parse_lat("56  15  30  N") == 56.25833333333333
        assert parse_lat("\t56°15′30″\n") == 56.25833333333333
    
    def test_parse_lat_case_insensitive(self):
        """Тест нечувствительности к регистру"""
        assert parse_lat("56.25n") == 56.25
        assert parse_lat("56.25N") == 56.25
        assert parse_lat("56.25s") == -56.25
        assert parse_lat("56.25S") == -56.25
    
    def test_parse_lat_errors_out_of_range(self):
        """Тест ошибок при значениях вне диапазона"""
        with pytest.raises(CoordError, match="Широта вне диапазона"):
            parse_lat("91")
        
        with pytest.raises(CoordError, match="Широта вне диапазона"):
            parse_lat("-91")
        
        with pytest.raises(CoordError, match="Широта вне диапазона"):
            parse_lat("90 1")  # 90°1' > 90°
        
        with pytest.raises(CoordError, match="Широта вне диапазона"):
            parse_lat("180")
    
    def test_parse_lat_errors_invalid_format(self):
        """Тест ошибок при некорректном формате"""
        with pytest.raises(CoordError, match="Не найдено числовых компонентов"):
            parse_lat("")
        
        with pytest.raises(CoordError, match="Не найдено числовых компонентов"):
            parse_lat("N")
        
        with pytest.raises(CoordError, match="Не найдено числовых компонентов"):
            parse_lat("abc")
        
        with pytest.raises(CoordError, match="Минуты вне диапазона"):
            parse_lat("56 60")
        
        with pytest.raises(CoordError, match="Секунды вне диапазона"):
            parse_lat("56 30 60")
        
        with pytest.raises(CoordError, match="Слишком много компонентов"):
            parse_lat("56 30 15 10")
    
    def test_parse_lat_errors_conflicting_signs(self):
        """Тест ошибок при конфликте знаков"""
        # Конфликт: отрицательное число и северная широта
        with pytest.raises(CoordError, match="Конфликт знаков"):
            parse_lat("-56 N")
        
        # Конфликт: положительное число и южная широта (хотя это менее очевидный случай)
        # Но согласно логике функции, S означает отрицательное, а положительное число - положительное
        # Посмотрим, как это обрабатывается
        # Проверим, что согласованные знаки работают корректно
        assert parse_lat("-56 S") == -56.0  # отрицательное число и южная широта - согласованы
        assert parse_lat("56 S") == -56.0   # положительное число, но S делает его отрицательным
        assert parse_lat("56 N") == 56.0    # положительное число и северная широта - согласованы


class TestParseLon:
    """Тесты для функции parse_lon"""
    
    def test_parse_lon_decimal_degrees(self):
        """Тест парсинга долготы в десятичных градусах"""
        assert parse_lon("37.617") == 37.617
        assert parse_lon("-122.383") == -122.383
        assert parse_lon("0.0") == 0.0
        assert parse_lon("180") == 180.0
        assert parse_lon("-180") == -180.0
    
    def test_parse_lon_with_hemisphere_letters(self):
        """Тест парсинга долготы с буквами полушария"""
        assert parse_lon("37.617E") == 37.617
        assert parse_lon("37.617 E") == 37.617
        assert parse_lon("122.383W") == -122.383
        assert parse_lon("122.383 W") == -122.383
        assert parse_lon("e37.617") == 37.617
        assert parse_lon("w122.383") == -122.383
    
    def test_parse_lon_degrees_minutes(self):
        """Тест парсинга долготы в градусах и минутах"""
        assert parse_lon("37 37") == 37.61666666666667  # 37°37' = 37 + 37/60
        assert parse_lon("37°37′") == 37.61666666666667
        assert parse_lon("37:37") == 37.61666666666667
        assert parse_lon("37 37 E") == 37.61666666666667
        assert parse_lon("122 23 W") == -122.38333333333334
        assert parse_lon("-122 23") == -122.38333333333334
    
    def test_parse_lon_degrees_minutes_seconds(self):
        """Тест парсинга долготы в градусах, минутах и секундах"""
        assert parse_lon("37 37 0") == 37.61666666666667  # 37°37'0"
        assert parse_lon("37°37′0″") == 37.61666666666667
        assert parse_lon("37:37:0") == 37.61666666666667
        assert parse_lon("122 22 58 W") == -122.38277777777777
        assert parse_lon("-122 22 58") == -122.38277777777777
    
    def test_parse_lon_mixed_formats(self):
        """Тест различных смешанных форматов"""
        assert parse_lon("37e37.0") == 37.61666666666667  # 37°37.0'E
        assert parse_lon("122w23") == -122.38333333333334  # 122°23'W
        assert parse_lon("37 37.5") == 37.625  # 37°37.5'
    
    def test_parse_lon_boundary_values(self):
        """Тест граничных значений долготы"""
        assert parse_lon("180") == 180.0
        assert parse_lon("-180") == -180.0
        assert parse_lon("180 E") == 180.0
        assert parse_lon("180 W") == -180.0
        assert parse_lon("0") == 0.0
    
    def test_parse_lon_whitespace_handling(self):
        """Тест обработки пробелов"""
        assert parse_lon("  37.617  ") == 37.617
        assert parse_lon("37  37  0  E") == 37.61666666666667
        assert parse_lon("\t37°37′0″\n") == 37.61666666666667
    
    def test_parse_lon_case_insensitive(self):
        """Тест нечувствительности к регистру"""
        assert parse_lon("37.617e") == 37.617
        assert parse_lon("37.617E") == 37.617
        assert parse_lon("122.383w") == -122.383
        assert parse_lon("122.383W") == -122.383
    
    def test_parse_lon_errors_out_of_range(self):
        """Тест ошибок при значениях вне диапазона"""
        with pytest.raises(CoordError, match="Долгота вне диапазона"):
            parse_lon("181")
        
        with pytest.raises(CoordError, match="Долгота вне диапазона"):
            parse_lon("-181")
        
        with pytest.raises(CoordError, match="Долгота вне диапазона"):
            parse_lon("180 1")  # 180°1' > 180°
        
        with pytest.raises(CoordError, match="Долгота вне диапазона"):
            parse_lon("360")
    
    def test_parse_lon_errors_invalid_format(self):
        """Тест ошибок при некорректном формате"""
        with pytest.raises(CoordError, match="Не найдено числовых компонентов"):
            parse_lon("")
        
        with pytest.raises(CoordError, match="Не найдено числовых компонентов"):
            parse_lon("E")
        
        with pytest.raises(CoordError, match="Не найдено числовых компонентов"):
            parse_lon("xyz")
        
        with pytest.raises(CoordError, match="Минуты вне диапазона"):
            parse_lon("37 60")
        
        with pytest.raises(CoordError, match="Секунды вне диапазона"):
            parse_lon("37 30 60")
        
        with pytest.raises(CoordError, match="Слишком много компонентов"):
            parse_lon("37 30 15 10")
    
    def test_parse_lon_errors_conflicting_signs(self):
        """Тест ошибок при конфликте знаков"""
        # Конфликт: отрицательное число и восточная долгота
        with pytest.raises(CoordError, match="Конфликт знаков"):
            parse_lon("-122 E")
        
        # Проверим, что согласованные знаки работают корректно
        assert parse_lon("-122 W") == -122.0  # отрицательное число и западная долгота - согласованы
        assert parse_lon("122 W") == -122.0   # положительное число, но W делает его отрицательным
        assert parse_lon("122 E") == 122.0    # положительное число и восточная долгота - согласованы


class TestSpecialCases:
    """Тесты для особых случаев и граничных условий"""
    
    def test_decimal_precision(self):
        """Тест точности десятичных вычислений"""
        # Проверим, что минуты и секунды правильно конвертируются в десятичные градусы
        result = parse_lat("56 15 30")  # 56 + 15/60 + 30/3600 = 56.25833333333333
        expected = 56 + 15/60 + 30/3600
        assert abs(result - expected) < 1e-10
    
    def test_zero_minutes_seconds(self):
        """Тест с нулевыми минутами и секундами"""
        assert parse_lat("56 0 0") == 56.0
        assert parse_lon("37 0 0") == 37.0
        assert parse_lat("56 0") == 56.0
        assert parse_lon("37 0") == 37.0
    
    def test_floating_point_minutes_seconds(self):
        """Тест с дробными минутами и секундами"""
        assert parse_lat("56 15.5") == 56 + 15.5/60
        assert parse_lon("37 30.25") == 37 + 30.25/60
        assert parse_lat("56 15 30.5") == 56 + 15/60 + 30.5/3600
    
    def test_various_separators(self):
        """Тест различных разделителей"""
        # Все эти варианты должны давать одинаковый результат
        expected_lat = 56.25833333333333
        formats = [
            "56 15 30",
            "56°15′30″",
            "56:15:30",
            # "56-15-30",  # минус будет интерпретирован как знак числа, не как разделитель
            "56/15/30",
            "56_15_30"
        ]
        
        for fmt in formats:
            result = parse_lat(fmt)
            assert abs(result - expected_lat) < 1e-10, f"Failed for format: {fmt}"
    
    def test_edge_cases_minutes_seconds(self):
        """Тест граничных случаев для минут и секунд"""
        # Максимальные допустимые значения
        assert parse_lat("56 59 59") == 56 + 59/60 + 59/3600
        assert parse_lon("37 59 59") == 37 + 59/60 + 59/3600
        
        # Минимальные значения
        assert parse_lat("56 0 0") == 56.0
        assert parse_lon("37 0 0") == 37.0
        
        # Дробные значения близко к границе
        assert parse_lat("56 59.999") == 56 + 59.999/60
        assert parse_lat("56 59 59.999") == 56 + 59/60 + 59.999/3600
    
    def test_extreme_coordinates(self):
        """Тест экстремальных координат"""
        # Полюса
        assert parse_lat("90 N") == 90.0
        assert parse_lat("90 S") == -90.0
        
        # Международная линия смены дат
        assert parse_lon("180 E") == 180.0
        assert parse_lon("180 W") == -180.0
        
        # Гринвичский меридиан и экватор
        assert parse_lat("0") == 0.0
        assert parse_lon("0") == 0.0
    
    def test_real_world_coordinates(self):
        """Тест реальных географических координат"""
        # Москва: 55°45′21″N 37°37′2″E
        moscow_lat = parse_lat("55 45 21 N")
        moscow_lon = parse_lon("37 37 2 E")
        assert abs(moscow_lat - 55.7558333) < 1e-6
        assert abs(moscow_lon - 37.6172222) < 1e-6
        
        # Нью-Йорк: 40°42′46″N 74°0′21″W
        ny_lat = parse_lat("40 42 46 N")
        ny_lon = parse_lon("74 0 21 W")
        assert abs(ny_lat - 40.7127778) < 1e-6
        assert abs(ny_lon - (-74.0058333)) < 1e-6
        
        # Сидней: 33°52′04″S 151°12′36″E
        sydney_lat = parse_lat("33 52 4 S")
        sydney_lon = parse_lon("151 12 36 E")
        assert abs(sydney_lat - (-33.8677778)) < 1e-6
        assert abs(sydney_lon - 151.21) < 1e-6
        
    def test_decimal_seconds(self):
        """Тест с десятичными секундами"""
        assert parse_lat('''56°15′30.5"''') == 56 + 15/60 + 30.5/3600
        assert parse_lon('''37°30′15.75"''') == 37 + 30/60 + 15.75/3600
        
class TestToStr:
    """Тесты для строкового представления координат"""
    
    def test_latitude_str(self):
        """Тест строкового представления широты"""
        from pyastro.util import Latitude
        lat = Latitude(56.2583333)
        assert str(lat) == "56.258333° N"
        assert format(lat, ".2f") == "56°15'30.00\"N"
        
        lat_neg = Latitude(-33.8677778)
        assert str(lat_neg) == "33.867778° S"
        assert format(lat_neg, "06.3f") == "33°52'04.000\"S"

    def test_longitude_str(self):
        """Тест строкового представления долготы"""
        from pyastro.util import Longitude
        lon = Longitude(37.6172222)
        assert str(lon) == "37.617222° E"
        assert format(lon, "05.2f") == "37°37'02.00\"E"
        
        lon_neg = Longitude(-122.3827778)
        assert str(lon_neg) == "122.382778° W"
        assert format(lon_neg, "06.3f") == "122°22'58.000\"W"