# all_segments
{   'end_time': Timestamp('2018-10-08 21:55:50'),
        'final_state': 'ACTIVE',
        'page_visits': 6,
        'segment_id': 2,
        'slot_id': 56,
        'start_time': Timestamp('2018-10-08 21:12:03'),
        'tracker_counter_json': '{"akamai_technologies": 6, "atlas": 6, '
                                '"doubleclick": 6, "facebook": 6, "google": 6, '
                                '"google_analytics": 6, "imgur": 6, "twitter": '
                                '6}',
        'tracker_events': 48,
        'trigger': 'session_gap',
        'unique_domains': 1,
        'user_id': 224},

# rotation_trigger
Counter({   'session_gap': 789818,
            'rotation_threshold': 227239,
            'end_of_stream': 63077})


# Segments_sorted
{   'end_time': Timestamp('2018-10-17 21:44:48'),
        'final_state': 'SATURATED',
        'page_visits': 44,
        'segment_id': 4,
        'slot_id': 16,
        'start_time': Timestamp('2018-10-17 21:37:10'),
        'tracker_counter_json': '{"appnexus": 44, "bing_ads": 44, '
                                '"contentsquare.net": 44, "doubleclick": 44, '
                                '"facebook": 44, "google": 44, '
                                '"google_adservices": 44, "google_analytics": '
                                '44, "google_syndication": 44, '
                                '"google_tag_manager": 44, "kairion.de": 44, '
                                '"new_relic": 44, "s24_com": 44, "speedcurve": '
                                '44, "the_adex": 44}',
        'tracker_events': 660,
        'trigger': 'rotation_threshold',
        'unique_domains': 1,
        'user_id': 63},

# user_chunks
user_chunks = [
    (
        "user_101",
        1,
        2148,
        df_user_101,
        <PipelineConfig num_slots=5 ...>,
        {"google.com": ["doubleclick.net"]},
        False
    ),
    (
        "user_102",
        2,
        2148,
        df_user_102,
        <PipelineConfig num_slots=5 ...>,
        {"google.com": ["doubleclick.net"]},
        False
    ),]

# query_matrix
Segment 0
[[0.19245009 0.19245009 0.19245009 0.19245009 0.19245009 0.19245009
  0.19245009 0.         0.         0.19245009 0.19245009 0.19245009
  0.19245009 0.19245009 0.19245009 0.19245009 0.         0.
  0.         0.19245009 0.         0.         0.19245009 0.
  0.         0.19245009 0.         0.         0.         0.19245009
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.19245009
  0.         0.19245009 0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.19245009 0.         0.         0.
  0.         0.19245009 0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.19245009 0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.19245009 0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.19245009 0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.19245009 0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.19245009 0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.         0.         0.         0.         0.         0.
  0.        ]]

$$\text{inv\_norms} = \begin{pmatrix}  \mathbf{\frac{1}{\text{Norm}_0}} & 0 & 0 & \dots \\  0 & \mathbf{\frac{1}{\text{Norm}_1}} & 0 & \dots \\  0 & 0 & \mathbf{\frac{1}{\text{Norm}_2}} & \dots \\  \vdots & \vdots & \vdots & \ddots  \end{pmatrix}$$


# tracker_to_index
{   '1000mercis': 552,
    '161media': 200,
    '1dmp.io': 332,
    '1plusx': 396,
    '1und1': 532,
    '24smi': 628,
    'a3cloud_net': 554,
    'ab_tasty': 159,
    'ablida': 477,
    'accengage': 485,
    'acpm.fr': 557,
    'acuity_ads': 766,
    'acxiom': 324,
    'ad4mat': 175,
    'ad_spirit': 322,
    'adality_gmbh': 91,
    'adap.tv': 536,
    'adara_analytics': 212,
    'adbetclickin.pink': 583,
    'adblade.com': 455,
    'adbrain': 466,
    'adc_media': 250,
    'adclear': 514,
    'addthis': 38,
    'adelphic': 374,
    'adform': 16,
    'adfox': 272,
    'adgear': 570,
    'adglare.net': 468,
    'adglue': 461,
}

# In query matrix

Matrix-Form (Shape): (1044312, 769) -> (Segmente, Vokabular-Größe)
Anzahl gespeicherter Elemente (nnz): 18658534
Typ der Matrix: <class 'scipy.sparse._csr.csr_matrix'>

Untersuche die ersten 5 echten Segmente im Datensatz:

--- Segment Index 0 ---
Aktive Tracker in diesem Segment: 7
Beispiel-Werte (erste 5 Tracker):
  -> Tracker ID 6: L2-Wert = 0.3780
  -> Tracker ID 5: L2-Wert = 0.3780
  -> Tracker ID 4: L2-Wert = 0.3780
  -> Tracker ID 3: L2-Wert = 0.3780
  -> Tracker ID 2: L2-Wert = 0.3780
  [Check] Berechnete Vektorlänge (L2-Norm): 1.0000

--- Segment Index 1 ---
Aktive Tracker in diesem Segment: 0
  -> Dieses Segment hat keine Tracker-Events (vollständig leer / 0).

--- Segment Index 2 ---
Aktive Tracker in diesem Segment: 0
  -> Dieses Segment hat keine Tracker-Events (vollständig leer / 0).

--- Segment Index 3 ---
Aktive Tracker in diesem Segment: 0
  -> Dieses Segment hat keine Tracker-Events (vollständig leer / 0).

--- Segment Index 4 ---
Aktive Tracker in diesem Segment: 0
  -> Dieses Segment hat keine Tracker-Events (vollständig leer / 0).
==================================================