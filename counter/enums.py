from enum import Enum

class SurfQualityRating(Enum):
    POOR = "Poor"
    POOR_TO_FAIR = "Poor to Fair"
    FAIR = "Fair"
    FAIR_TO_GOOD = "Fair to Good"
    GOOD = "Good"


class DayIdentifierEnum(Enum):
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6

    class Labels:
        MONDAY = "Monday"
        TUESDAY = "Tuesday"
        WEDNESDAY = "Wednesday"
        THURSDAY = "Thursday"
        FRIDAY = "Friday"
        SATURDAY = "Saturday"
        SUNDAY = "Sunday"


class MonthIdentifierEnum(Enum):
    JANUARY = 1
    FEBRUARY = 2
    MARCH = 3
    APRIL = 4
    MAY = 5
    JUNE = 6
    JULY = 7
    AUGUST = 8
    SEPTEMBER = 9
    OCTOBER = 10
    NOVEMBER = 11
    DECEMBER = 12

    class Labels:
        JANUARY = "January"
        FEBRUARY = "February"
        MARCH = "March"
        APRIL = "April"
        MAY = "May"
        JUNE = "June"
        JULY = "July"
        AUGUST = "August"
        SEPTEMBER = "September"
        OCTOBER = "October"
        NOVEMBER = "November"
        DECEMBER = "December"


class HourIdentifierEnum(Enum):
    HR_00 = 0
    HR_01 = 1
    HR_02 = 2
    HR_03 = 3
    HR_04 = 4
    HR_05 = 5
    HR_06 = 6
    HR_07 = 7
    HR_08 = 8
    HR_09 = 9
    HR_10 = 10
    HR_11 = 11
    HR_12 = 12
    HR_14 = 14
    HR_13 = 13
    HR_15 = 15
    HR_16 = 16
    HR_17 = 17
    HR_18 = 18
    HR_19 = 19
    HR_20 = 20
    HR_21 = 21
    HR_22 = 22
    HR_23 = 23

    class Labels:
        HR_00 = "12AM"
        HR_01 = "1AM"
        HR_02 = "2AM"
        HR_03 = "3AM"
        HR_04 = "4AM"
        HR_05 = "5AM"
        HR_06 = "6AM"
        HR_07 = "7AM"
        HR_08 = "8AM"
        HR_09 = "9AM"
        HR_10 = "10AM"
        HR_11 = "11AM"
        HR_12 = "12PM"
        HR_14 = "1PM"
        HR_13 = "2PM"
        HR_15 = "3M"
        HR_16 = "4PM"
        HR_17 = "5PM"
        HR_18 = "6PM"
        HR_19 = "7PM"
        HR_20 = "8PM"
        HR_21 = "9PM"
        HR_22 = "10PM"
        HR_23 = "11PM"
