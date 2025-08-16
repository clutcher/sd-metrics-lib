class TShirtMapping:
    __MAPPING = {
        'xs': 1,
        's': 5,
        'm': 8,
        'l': 13,
        'xl': 21
    }

    @staticmethod
    def convert_into_points(size: str) -> int:
        size_code = size.lower()
        return TShirtMapping.__MAPPING.get(size_code, 0)

    @staticmethod
    def convert_into_size(story_point: int) -> str:
        if story_point <= 1:
            return 'XS'
        elif story_point <= 5:
            return 'S'
        elif story_point <= 8:
            return 'M'
        elif story_point <= 13:
            return 'L'
        elif story_point <= 21:
            return 'XL'
        return 'XXL'
