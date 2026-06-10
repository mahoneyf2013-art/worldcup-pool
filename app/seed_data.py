"""Seeded 2026 World Cup data: groups, the 72 group fixtures (with dates), and the
knockout skeleton (teams filled in as the bracket resolves). Names match the scoring engine."""
GROUPS = {
 "A": [
  "Mexico",
  "South Africa",
  "South Korea",
  "Czechia"
 ],
 "B": [
  "Canada",
  "Bosnia & Herzegovina",
  "Qatar",
  "Switzerland"
 ],
 "C": [
  "Brazil",
  "Morocco",
  "Haiti",
  "Scotland"
 ],
 "D": [
  "United States",
  "Paraguay",
  "Australia",
  "Turkiye"
 ],
 "E": [
  "Germany",
  "Curacao",
  "Ivory Coast",
  "Ecuador"
 ],
 "F": [
  "Netherlands",
  "Japan",
  "Sweden",
  "Tunisia"
 ],
 "G": [
  "Belgium",
  "Egypt",
  "Iran",
  "New Zealand"
 ],
 "H": [
  "Spain",
  "Cape Verde",
  "Saudi Arabia",
  "Uruguay"
 ],
 "I": [
  "France",
  "Senegal",
  "Iraq",
  "Norway"
 ],
 "J": [
  "Argentina",
  "Algeria",
  "Austria",
  "Jordan"
 ],
 "K": [
  "Portugal",
  "DR Congo",
  "Uzbekistan",
  "Colombia"
 ],
 "L": [
  "England",
  "Croatia",
  "Ghana",
  "Panama"
 ]
}

# (date, group, team_a, team_b)
GROUP_FIXTURES = [
  ('2026-06-11', 'A', 'Mexico', 'South Africa'),
  ('2026-06-11', 'A', 'Czechia', 'South Korea'),
  ('2026-06-12', 'B', 'Canada', 'Bosnia & Herzegovina'),
  ('2026-06-12', 'D', 'United States', 'Paraguay'),
  ('2026-06-13', 'D', 'Turkiye', 'Australia'),
  ('2026-06-13', 'B', 'Switzerland', 'Qatar'),
  ('2026-06-13', 'C', 'Brazil', 'Morocco'),
  ('2026-06-13', 'C', 'Scotland', 'Haiti'),
  ('2026-06-14', 'E', 'Germany', 'Curacao'),
  ('2026-06-14', 'F', 'Netherlands', 'Japan'),
  ('2026-06-14', 'E', 'Ecuador', 'Ivory Coast'),
  ('2026-06-14', 'F', 'Sweden', 'Tunisia'),
  ('2026-06-15', 'H', 'Spain', 'Cape Verde'),
  ('2026-06-15', 'G', 'Belgium', 'Egypt'),
  ('2026-06-15', 'H', 'Uruguay', 'Saudi Arabia'),
  ('2026-06-15', 'G', 'Iran', 'New Zealand'),
  ('2026-06-16', 'J', 'Austria', 'Jordan'),
  ('2026-06-16', 'I', 'France', 'Senegal'),
  ('2026-06-16', 'I', 'Norway', 'Iraq'),
  ('2026-06-16', 'J', 'Argentina', 'Algeria'),
  ('2026-06-17', 'K', 'Portugal', 'DR Congo'),
  ('2026-06-17', 'L', 'England', 'Croatia'),
  ('2026-06-17', 'L', 'Panama', 'Ghana'),
  ('2026-06-17', 'K', 'Colombia', 'Uzbekistan'),
  ('2026-06-18', 'A', 'Czechia', 'South Africa'),
  ('2026-06-18', 'B', 'Switzerland', 'Bosnia & Herzegovina'),
  ('2026-06-18', 'B', 'Canada', 'Qatar'),
  ('2026-06-18', 'A', 'Mexico', 'South Korea'),
  ('2026-06-19', 'D', 'United States', 'Australia'),
  ('2026-06-19', 'C', 'Morocco', 'Scotland'),
  ('2026-06-19', 'C', 'Brazil', 'Haiti'),
  ('2026-06-19', 'D', 'Turkiye', 'Paraguay'),
  ('2026-06-20', 'F', 'Japan', 'Tunisia'),
  ('2026-06-20', 'F', 'Netherlands', 'Sweden'),
  ('2026-06-20', 'E', 'Germany', 'Ivory Coast'),
  ('2026-06-20', 'E', 'Ecuador', 'Curacao'),
  ('2026-06-21', 'H', 'Spain', 'Saudi Arabia'),
  ('2026-06-21', 'G', 'Belgium', 'Iran'),
  ('2026-06-21', 'H', 'Uruguay', 'Cape Verde'),
  ('2026-06-21', 'G', 'Egypt', 'New Zealand'),
  ('2026-06-22', 'J', 'Argentina', 'Austria'),
  ('2026-06-22', 'I', 'France', 'Iraq'),
  ('2026-06-22', 'I', 'Norway', 'Senegal'),
  ('2026-06-22', 'J', 'Algeria', 'Jordan'),
  ('2026-06-23', 'K', 'Portugal', 'Uzbekistan'),
  ('2026-06-23', 'L', 'England', 'Ghana'),
  ('2026-06-23', 'L', 'Croatia', 'Panama'),
  ('2026-06-23', 'K', 'Colombia', 'DR Congo'),
  ('2026-06-24', 'B', 'Canada', 'Switzerland'),
  ('2026-06-24', 'B', 'Bosnia & Herzegovina', 'Qatar'),
  ('2026-06-24', 'C', 'Brazil', 'Scotland'),
  ('2026-06-24', 'C', 'Morocco', 'Haiti'),
  ('2026-06-24', 'A', 'Mexico', 'Czechia'),
  ('2026-06-24', 'A', 'South Korea', 'South Africa'),
  ('2026-06-25', 'E', 'Ivory Coast', 'Curacao'),
  ('2026-06-25', 'E', 'Germany', 'Ecuador'),
  ('2026-06-25', 'F', 'Japan', 'Sweden'),
  ('2026-06-25', 'F', 'Netherlands', 'Tunisia'),
  ('2026-06-25', 'D', 'United States', 'Turkiye'),
  ('2026-06-25', 'D', 'Paraguay', 'Australia'),
  ('2026-06-26', 'I', 'France', 'Norway'),
  ('2026-06-26', 'I', 'Senegal', 'Iraq'),
  ('2026-06-26', 'H', 'Saudi Arabia', 'Cape Verde'),
  ('2026-06-26', 'H', 'Spain', 'Uruguay'),
  ('2026-06-26', 'G', 'Egypt', 'Iran'),
  ('2026-06-26', 'G', 'Belgium', 'New Zealand'),
  ('2026-06-27', 'L', 'England', 'Panama'),
  ('2026-06-27', 'L', 'Croatia', 'Ghana'),
  ('2026-06-27', 'K', 'Portugal', 'Colombia'),
  ('2026-06-27', 'K', 'Uzbekistan', 'DR Congo'),
  ('2026-06-27', 'J', 'Argentina', 'Jordan'),
  ('2026-06-27', 'J', 'Austria', 'Algeria'),
]

# (date, round)  -- teams TBD until the bracket resolves
KO_SKELETON = [
  ('2026-06-28', 'R32'),
  ('2026-06-29', 'R32'),
  ('2026-06-30', 'R32'),
  ('2026-07-01', 'R32'),
  ('2026-07-02', 'R32'),
  ('2026-07-03', 'R32'),
  ('2026-06-28', 'R32'),
  ('2026-06-29', 'R32'),
  ('2026-06-30', 'R32'),
  ('2026-07-01', 'R32'),
  ('2026-07-02', 'R32'),
  ('2026-07-03', 'R32'),
  ('2026-06-28', 'R32'),
  ('2026-06-29', 'R32'),
  ('2026-06-30', 'R32'),
  ('2026-07-01', 'R32'),
  ('2026-07-04', 'R16'),
  ('2026-07-05', 'R16'),
  ('2026-07-06', 'R16'),
  ('2026-07-07', 'R16'),
  ('2026-07-04', 'R16'),
  ('2026-07-05', 'R16'),
  ('2026-07-06', 'R16'),
  ('2026-07-07', 'R16'),
  ('2026-07-09', 'QF'),
  ('2026-07-10', 'QF'),
  ('2026-07-10', 'QF'),
  ('2026-07-11', 'QF'),
  ('2026-07-14', 'SF'),
  ('2026-07-15', 'SF'),
  ('2026-07-18', '3rd'),
  ('2026-07-19', 'Final'),
]
