import re
from fastapi import HTTPException
from sqlalchemy.orm import Session
from fastapi.responses import Response
from io import BytesIO
from app.modules.assessments.models.assessment_model import AssessmentSubmission, RawEvent

# Disorder to questionnaire mapping
DISORDER_MAPPING = {
    "autismspectrumdisorderasd": "AQ-10",
    "attentiondeficithyperactivitydisorderadhd": "ASRS",
    "anxiety": "GAD-7",
    "depression": "PHQ-9",
    "obsessivecompulsivedisorderocd": "Y-BOCS",
    "posttraumaticstressdisorderptsd": "PCL-5",
    "alcoholusedisorder": "AUDIT",
    "drugusedisorder": "DAST",
    "bipolar": "Mood Disorder Questionnaire",
    "borderlinepersonalitydisorderbpd": "MSI-BPD",
    "eatingdisorder": "EAT-26"
}

# Questionnaire database
QUESTIONNAIRES = {
    "GAD-7": {
        "name": "GAD-7",
        "testname":"GAD-7",
        "instructions":"Over the last two weeks, how often have you been bothered by the following problems?",
        "questions": [
            {"id": 1, "text": "Feeling nervous, anxious, or on edge", "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"]},
            {"id": 2, "text": "Not being able to stop or control worrying", "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"]},
            {"id": 3, "text": "Worrying too much about different things", "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"]},
            {"id": 4, "text": "Trouble relaxing", "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"]},
            {"id": 5, "text": "Being so restless that it is hard to sit still", "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"]},
            {"id": 6, "text": "Becoming easily annoyed or irritable", "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"]},
            {"id": 7, "text": "Feeling afraid, as if something awful might happen", "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"]},
            {"id": 8, "text": "If you checked any problems, how difficult have they made it for you to do your work, take care of things at home, or get along with other people?", "options": ["Not difficult at all", "Somewhat difficult", "Very difficult", "Extremely difficult"]}
        ]
    },
    "PHQ-9": {
        "name": "PHQ-9",
        "testname":"PHQ-9",
        "instructions":"Over the last 2 weeks, how often have you been bothered by any of the following problems?",
        "questions": [
            {"id": 1, "text": "Little interest or pleasure in doing things", "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"]},
            {"id": 2, "text": "Feeling down, depressed, or hopeless", "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"]},
            {"id": 3, "text": "Trouble falling or staying asleep, or sleeping too much", "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"]},
            {"id": 4, "text": "Feeling tired or having little energy", "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"]},
            {"id": 5, "text": "Poor appetite or overeating", "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"]},
            {"id": 6, "text": "Feeling bad about yourself—or that you are a failure or have let yourself or your family down", "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"]},
            {"id": 7, "text": "Trouble concentrating on things, such as reading the newspaper or watching television", "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"]},
            {"id": 8, "text": "Moving or speaking so slowly that other people could have noticed. Or the opposite — being so fidgety or restless that you have been moving around a lot more than usual", "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"]},
            {"id": 9, "text": "Thoughts that you would be better off dead, or of hurting yourself", "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"]},
            {"id": 10, "text": "If you checked off any problems, how difficult have these problems made it for you to do your work, take care of things at home, or get along with other people?", "options": ["Not difficult at all", "Somewhat difficult", "Very difficult", "Extremely difficult"]}
        ]
    },
    "AQ-10": {
        "name": "Autism Spectrum Quotient (AQ-10)",
        "testname":"AQ-10",
        "instrcutions":"Please read each statement and select the option that best describes you.",
        "questions": [
            {"id": 1, "text": "I often notice small sounds when others do not", "options": ["Definitely Agree", "Slightly Agree", "Slightly Disagree", "Definitely Disagree"]},
            {"id": 2, "text": "I usually concentrate more on the whole picture, rather than the small details", "options": ["Definitely Agree", "Slightly Agree", "Slightly Disagree", "Definitely Disagree"]},
            {"id": 3, "text": "I find it easy to do more than one thing at once", "options": ["Definitely Agree", "Slightly Agree", "Slightly Disagree", "Definitely Disagree"]},
            {"id": 4, "text": "If there is an interruption, I can switch back to what I was doing very quickly", "options": ["Definitely Agree", "Slightly Agree", "Slightly Disagree", "Definitely Disagree"]},
            {"id": 5, "text": "I find it easy to 'read between the lines' when someone is talking to me", "options": ["Definitely Agree", "Slightly Agree", "Slightly Disagree", "Definitely Disagree"]},
            {"id": 6, "text": "I know how to tell if someone listening to me is getting bored", "options": ["Definitely Agree", "Slightly Agree", "Slightly Disagree", "Definitely Disagree"]},
            {"id": 7, "text": "When I'm reading a story I find it difficult to work out the characters' intentions", "options": ["Definitely Agree", "Slightly Agree", "Slightly Disagree", "Definitely Disagree"]},
            {"id": 8, "text": "I like to collect information about categories of things (e.g. types of car, types of bird, types of train, types of plant etc)", "options": ["Definitely Agree", "Slightly Agree", "Slightly Disagree", "Definitely Disagree"]},
            {"id": 9, "text": "I find it easy to work out what someone is thinking or feeling just by looking at their face", "options": ["Definitely Agree", "Slightly Agree", "Slightly Disagree", "Definitely Disagree"]},
            {"id": 10, "text": "I find it difficult to work out people's intentions", "options": ["Definitely Agree", "Slightly Agree", "Slightly Disagree", "Definitely Disagree"]}
        ]
    },
    "Mood Disorder Questionnaire": {
        "name": "Mood Disorder Questionnaire (MDQ)",
        "testname":"Mood Disorder Questionnaire",
        "instructions":"Check ( 3) the answer that best applies to you. Please answer each question as best you can.",
        "questions": [
            {"id": 1, "text": "Has there ever been a period of time when you were not your usual self and you felt so good or so hyper that other people thought you were not your normal self or you were so hyper that you got into trouble?", "options": ["Yes", "No"]},
            {"id": 2, "text": "Has there ever been a period of time when you were not your usual self and you were so irritable that you shouted at people or started fights or arguments?", "options": ["Yes", "No"]},
            {"id": 3, "text": "Has there ever been a period of time when you were not your usual self and you felt much more self-confident than usual?", "options": ["Yes", "No"]},
            {"id": 4, "text": "Has there ever been a period of time when you were not your usual self and you got much less sleep than usual and found you didn't really miss it?", "options": ["Yes", "No"]},
            {"id": 5, "text": "Has there ever been a period of time when you were not your usual self and you were much more talkative or spoke faster than usual?", "options": ["Yes", "No"]},
            {"id": 6, "text": "Has there ever been a period of time when you were not your usual self and thoughts raced through your head or you couldn't slow your mind down?", "options": ["Yes", "No"]},
            {"id": 7, "text": "Has there ever been a period of time when you were not your usual self and you were so easily distracted by things around you that you had trouble concentrating or staying on track?", "options": ["Yes", "No"]},
            {"id": 8, "text": "Has there ever been a period of time when you were not your usual self and you had much more energy than usual?", "options": ["Yes", "No"]},
            {"id": 9, "text": "Has there ever been a period of time when you were not your usual self and you were much more active or did many more things than usual?", "options": ["Yes", "No"]},
            {"id": 10, "text": "Has there ever been a period of time when you were not your usual self and you were much more social or outgoing than usual, for example, you telephoned friends in the middle of the night?", "options": ["Yes", "No"]},
            {"id": 11, "text": "Has there ever been a period of time when you were not your usual self and you were much more interested in sex than usual?", "options": ["Yes", "No"]},
            {"id": 12, "text": "Has there ever been a period of time when you were not your usual self and you did things that were unusual for you or that other people might have thought were excessive, foolish, or risky?", "options": ["Yes", "No"]},
            {"id": 13, "text": "Has there ever been a period of time when you were not your usual self and spending money got you or your family in trouble?", "options": ["Yes", "No"]},
            {"id": 14, "text": "If you checked YES to more than one of the above, have several of these ever happened during the same period of time?", "options": ["Yes", "No"]},
            {"id": 15, "text": "How much of a problem did any of these cause you — like being able to work; having family, money, or legal troubles; getting into arguments or fights?", "options": ["No problem", "Minor problem", "Moderate problem", "Serious problem"]},
            {"id": 16, "text": "Have any of your blood relatives (ie, children, siblings, parents, grandparents, aunts, uncles) had manic-depressive illness or bipolar disorder?", "options": ["Yes", "No"]},
            {"id": 17, "text": "Has a health professional ever told you that you have manic-depressive illness or bipolar disorder?", "options": ["Yes", "No"]}
        ]
    },
    "ASRS": {
        "name": "Adult ADHD Self-Report Scale (ASRS)",
        "testname":"ASRS",
        "instructions":"Please read each statement and select the option that best reflects your experiences. Think about how you have felt and behaved over the past 6 months to make your selection.",
        "questions": [
            {"id": 1, "text": "How often do you have trouble wrapping up the final details of a project, once the challenging parts have been done?", "options": ["Never", "Rarely", "Sometimes", "Often", "Very Often"]},
            {"id": 2, "text": "How often do you have difficulty getting things in order when you have to do a task that requires organization?", "options": ["Never", "Rarely", "Sometimes", "Often", "Very Often"]},
            {"id": 3, "text": "How often do you have problems remembering appointments or obligations?", "options": ["Never", "Rarely", "Sometimes", "Often", "Very Often"]},
            {"id": 4, "text": "When you have a task that requires a lot of thought, how often do you avoid or delay getting started?", "options": ["Never", "Rarely", "Sometimes", "Often", "Very Often"]},
            {"id": 5, "text": "How often do you fidget or squirm with your hands or feet when you have to sit down for a long time?", "options": ["Never", "Rarely", "Sometimes", "Often", "Very Often"]},
            {"id": 6, "text": "How often do you feel overly active and compelled to do things, like you were driven by a motor?", "options": ["Never", "Rarely", "Sometimes", "Often", "Very Often"]},
            {"id": 7, "text": "How often do you make careless mistakes when you have to work on a boring or difficult project?", "options": ["Never", "Rarely", "Sometimes", "Often", "Very Often"]},
            {"id": 8, "text": "How often do you have difficulty keeping your attention when you are doing boring or repetitive work?", "options": ["Never", "Rarely", "Sometimes", "Often", "Very Often"]},
            {"id": 9, "text": "How often do you have difficulty concentrating on what people say to you, even when they are speaking to you directly?", "options": ["Never", "Rarely", "Sometimes", "Often", "Very Often"]},
            {"id": 10, "text": "How often do you misplace or have difficulty finding things at home or at work?", "options": ["Never", "Rarely", "Sometimes", "Often", "Very Often"]},
            {"id": 11, "text": "How often are you distracted by activity or noise around you?", "options": ["Never", "Rarely", "Sometimes", "Often", "Very Often"]},
            {"id": 12, "text": "How often do you leave your seat in meetings or other situations in which you are expected to remain seated?", "options": ["Never", "Rarely", "Sometimes", "Often", "Very Often"]},
            {"id": 13, "text": "How often do you feel restless or fidgety?", "options": ["Never", "Rarely", "Sometimes", "Often", "Very Often"]},
            {"id": 14, "text": "How often do you have difficulty unwinding and relaxing when you have time to yourself?", "options": ["Never", "Rarely", "Sometimes", "Often", "Very Often"]},
            {"id": 15, "text": "How often do you find yourself talking too much when you are in social situations?", "options": ["Never", "Rarely", "Sometimes", "Often", "Very Often"]},
            {"id": 16, "text": "When you're in a conversation, how often do you find yourself finishing the sentences of the people you are talking to, before they can finish them themselves?", "options": ["Never", "Rarely", "Sometimes", "Often", "Very Often"]},
            {"id": 17, "text": "How often do you have difficulty waiting your turn in situations when turn taking is required?", "options": ["Never", "Rarely", "Sometimes", "Often", "Very Often"]},
            {"id": 18, "text": "How often do you interrupt others when they are busy?", "options": ["Never", "Rarely", "Sometimes", "Often", "Very Often"]}
        ]
    },
    "EAT-26": {
        "name": "Eating Attitudes Test (EAT-26)",
        "testname": "EAT-26",
        "instructions":"This is a screening tool to help you determine if you might have an eating disorder. It is not a diagnosis and is not a substitute for professional medical advice.Please answer the questions as accurately and honestly as you can.",
        "questions": [
            # Part B Check a response for each of the following statements:
            {"id": 1, "text": "Am terrified about being overweight", "options": ["Always", "Usually", "Often", "Sometimes", "Rarely", "Never"]},
            {"id": 2, "text": "Avoid eating when I am hungry", "options": ["Always", "Usually", "Often", "Sometimes", "Rarely", "Never"]},
            {"id": 3, "text": "Find myself preoccupied with food", "options": ["Always", "Usually", "Often", "Sometimes", "Rarely", "Never"]},
            {"id": 4, "text": "Have gone on eating binges where I feel that I may not be able to stop", "options": ["Always", "Usually", "Often", "Sometimes", "Rarely", "Never"]},
            {"id": 5, "text": "Cut my food into small pieces", "options": ["Always", "Usually", "Often", "Sometimes", "Rarely", "Never"]},
            {"id": 6, "text": "Aware of the calorie content of foods that I eat", "options": ["Always", "Usually", "Often", "Sometimes", "Rarely", "Never"]},
            {"id": 7, "text": "Particularly avoid food with a high carbohydrate content", "options": ["Always", "Usually", "Often", "Sometimes", "Rarely", "Never"]},
            {"id": 8, "text": "Feel that others would prefer if I ate more", "options": ["Always", "Usually", "Often", "Sometimes", "Rarely", "Never"]},
            {"id": 9, "text": "Vomit after I have eaten", "options": ["Always", "Usually", "Often", "Sometimes", "Rarely", "Never"]},
            {"id": 10, "text": "Feel extremely guilty after eating", "options": ["Always", "Usually", "Often", "Sometimes", "Rarely", "Never"]},
            {"id": 11, "text": "Am preoccupied with a desire to be thinner", "options": ["Always", "Usually", "Often", "Sometimes", "Rarely", "Never"]},
            {"id": 12, "text": "Think about burning up calories when I exercise", "options": ["Always", "Usually", "Often", "Sometimes", "Rarely", "Never"]},
            {"id": 13, "text": "Other people think that I am too thin", "options": ["Always", "Usually", "Often", "Sometimes", "Rarely", "Never"]},
            {"id": 14, "text": "Am preoccupied with the thought of having fat on my body", "options": ["Always", "Usually", "Often", "Sometimes", "Rarely", "Never"]},
            {"id": 15, "text": "Take longer than others to eat my meals", "options": ["Always", "Usually", "Often", "Sometimes", "Rarely", "Never"]},
            {"id": 16, "text": "Avoid foods with sugar in them", "options": ["Always", "Usually", "Often", "Sometimes", "Rarely", "Never"]},
            {"id": 17, "text": "Eat diet foods", "options": ["Always", "Usually", "Often", "Sometimes", "Rarely", "Never"]},
            {"id": 18, "text": "Feel that food controls my life", "options": ["Always", "Usually", "Often", "Sometimes", "Rarely", "Never"]},
            {"id": 19, "text": "Display self-control around food", "options": ["Always", "Usually", "Often", "Sometimes", "Rarely", "Never"]},
            {"id": 20, "text": "Feel that others pressure me to eat", "options": ["Always", "Usually", "Often", "Sometimes", "Rarely", "Never"]},
            {"id": 21, "text": "Give too much time and thought to food", "options": ["Always", "Usually", "Often", "Sometimes", "Rarely", "Never"]},
            {"id": 22, "text": "Feel uncomfortable after eating sweets", "options": ["Always", "Usually", "Often", "Sometimes", "Rarely", "Never"]},
            {"id": 23, "text": "Engage in dieting behavior", "options": ["Always", "Usually", "Often", "Sometimes", "Rarely", "Never"]},
            {"id": 24, "text": "Like my stomach to be empty", "options": ["Always", "Usually", "Often", "Sometimes", "Rarely", "Never"]},
            {"id": 25, "text": "Have the impulse to vomit after meals", "options": ["Always", "Usually", "Often", "Sometimes", "Rarely", "Never"]},
            {"id": 26, "text": "Enjoy trying new rich foods", "options": ["Always", "Usually", "Often", "Sometimes", "Rarely", "Never"]},

            # Part C Behavioral Questions: the past 6 months have you:
            {"id": 27, "text": "Gone on eating binges where you feel that you may not be able to stop?", "options": ["Never", "Once a month or less", "2-3 times a month", "Once a week", "2-6 times a week", "Once a day or more"]},
            {"id": 28, "text": "Ever made yourself sick (vomited) to control your weight or shape?", "options": ["Never", "Once a month or less", "2-3 times a month", "Once a week", "2-6 times a week", "Once a day or more"]},
            {"id": 29, "text": "Ever used laxatives, diet pills or diuretics to control your weight or shape?", "options": ["Never", "Once a month or less", "2-3 times a month", "Once a week", "2-6 times a week", "Once a day or more"]},
            {"id": 30, "text": "Exercised more than 60 minutes a day to lose or to control your weight?", "options": ["Never", "Once a month or less", "2-3 times a month", "Once a week", "2-6 times a week", "Once a day or more"]},
            {"id": 31, "text": "Lost 20 pounds or more in the past 6 months", "options": ["Yes", "No"]}
        ]
    },
    "DAST": {
        "name": "Drug Abuse Screening Test (DAST)",
        "testname":"DAST",
        "instructions":"The following questions concern information about your involvement with drugs. Drug abuse refers to (1) the use of prescribed or “over-the-counter” drugs in excess of the directions, and (2) any non-medical use of drugs. Consider the past year (12 months) and carefully read each statement. Then decide whether your answer is YES or NO and check the appropriate space. Please be sure to answer every question.  ",
        "questions": [
            {"id": 1, "text": "Have you used drugs other than those required for medical reasons?", "options": ["Yes", "No"]},
            {"id": 2, "text": "Have you abused prescription drugs?", "options": ["Yes", "No"]},
            {"id": 3, "text": "Do you abuse more than one drug at a time?", "options": ["Yes", "No"]},
            {"id": 4, "text": "Can you get through the week without using drugs (other than those required for medical reasons)?", "options": ["Yes", "No"]},
            {"id": 5, "text": "Are you always able to stop using drugs when you want to?", "options": ["Yes", "No"]},
            {"id": 6, "text": "Do you abuse drugs on a continuous basis?", "options": ["Yes", "No"]},
            {"id": 7, "text": "Do you try to limit your drug use to certain situations?", "options": ["Yes", "No"]},
            {"id": 8, "text": "Have you had 'blackouts' or 'flashbacks' as a result of drug use?", "options": ["Yes", "No"]},
            {"id": 9, "text": "Do you ever feel bad about your drug abuse?", "options": ["Yes", "No"]},
            {"id": 10, "text": "Does your spouse (or parents) ever complain about your involvement with drugs?", "options": ["Yes", "No"]},
            {"id": 11, "text": "Do your friends or relatives know or suspect you abuse drugs?", "options": ["Yes", "No"]},
            {"id": 12, "text": "Has drug abuse ever created problems between you and your spouse?", "options": ["Yes", "No"]},
            {"id": 13, "text": "Has any family member ever sought help for problems related to your drug use?", "options": ["Yes", "No"]},
            {"id": 14, "text": "Have you ever lost friends because of your use of drugs?", "options": ["Yes", "No"]},
            {"id": 15, "text": "Have you ever neglected your family or missed work because of your use of drugs?", "options": ["Yes", "No"]},
            {"id": 16, "text": "Have you ever been in trouble at work because of drug abuse?", "options": ["Yes", "No"]},
            {"id": 17, "text": "Have you ever lost a job because of drug abuse?", "options": ["Yes", "No"]},
            {"id": 18, "text": "Have you gotten into fights when under the influence of drugs?", "options": ["Yes", "No"]},
            {"id": 19, "text": "Have you ever been arrested because of unusual behavior while under the influence of drugs?", "options": ["Yes", "No"]},
            {"id": 20, "text": "Have you ever been arrested for driving while under the influence of drugs?", "options": ["Yes", "No"]},
            {"id": 21, "text": "Have you engaged in illegal activities in order to obtain drugs?", "options": ["Yes", "No"]},
            {"id": 22, "text": "Have you ever been arrested for possession of illegal drugs?", "options": ["Yes", "No"]},
            {"id": 23, "text": "Have you ever experienced withdrawal symptoms as a result of heavy drug intake?", "options": ["Yes", "No"]},
            {"id": 24, "text": "Have you had medical problems as a result of your drug use?", "options": ["Yes", "No"]},
            {"id": 25, "text": "Have you ever gone to anyone for help for a drug problem?", "options": ["Yes", "No"]},
            {"id": 26, "text": "Have you ever been in a hospital for medical problems related to your drug use?", "options": ["Yes", "No"]},
            {"id": 27, "text": "Have you ever been involved in a treatment program specifically related to drug use?", "options": ["Yes", "No"]},
            {"id": 28, "text": "Have you been treated as an outpatient for problems related to drug abuse?", "options": ["Yes", "No"]}
        ]
    },
    "AUDIT": {
        "name": "Alcohol Use Disorders Identification Test (AUDIT)",
        "testname":"AUDIT",
        "instructions":"This test is a screening tool to help you understand your alcohol use. Please answer the 10 questions as honestly as you can, based on your experiences over the past year. Your answers are confidential.",
        "questions": [
            {"id": 1, "text": "How often do you have a drink containing alcohol?", "options": ["Never", "Monthly or less", "2-4 times a month", "2-3 times a week", "4 or more times a week"]},
            {"id": 2, "text": "How many drinks containing alcohol do you have on a typical day when you are drinking?", "options": ["0-2", "3 or 4", "5 or 6", "7-9", "10 or more"]},
            {"id": 3, "text": "How often do you have five or more drinks on one occasion?", "options": ["Never", "Less than monthly", "Monthly", "Weekly", "Daily or almost daily"]},
            {"id": 4, "text": "How often during the last year have you found that you were not able to stop drinking once you had started?", "options": ["Never", "Less than monthly", "Monthly", "Weekly", "Daily or almost daily"]},
            {"id": 5, "text": "How often during the last year have you failed to do what was normally expected of you because of drinking?", "options": ["Never", "Less than monthly", "Monthly", "Weekly", "Daily or almost daily"]},
            {"id": 6, "text": "How often during the last year have you needed a first drink in the morning to get yourself going after a heavy drinking session?", "options": ["Never", "Less than monthly", "Monthly", "Weekly", "Daily or almost daily"]},
            {"id": 7, "text": "How often during the last year have you had a feeling of guilt or remorse after drinking?", "options": ["Never", "Less than monthly", "Monthly", "Weekly", "Daily or almost daily"]},
            {"id": 8, "text": "How often during the last year have you been unable to remember what happened the night before because of your drinking?", "options": ["Never", "Less than monthly", "Monthly", "Weekly", "Daily or almost daily"]},
            {"id": 9, "text": "Have you or someone else been injured because of your drinking?", "options": ["No", "Yes, but not in the last year", "Yes, in the last year"]},
            {"id": 10, "text": "Has a relative, friend, doctor, or other health care worker been concerned about your drinking or suggested you cut down?", "options": ["No", "Yes, but not in the last year", "Yes, in the last year"]}
        ]
    },
    "Y-BOCS": {
  "name": "Yale-Brown Obsessive Compulsive Scale (Y-BOCS)",
  "testname":"Y-BOCS",
  "instructions":"Questions 1 to 5 are about your obsessive thoughts./nObsessions are unwanted ideas, images or impulses that intrude on thinking against your wishes and efforts to resist them.  They usually involve themes of harm, risk and danger.  Common obsessions are excessive fears of contamination; recurring doubts about danger, extreme concern with order, symmetry, or exactness; fear of losing important things. Please answer each question by circling the appropriate number.",
  "questions": [
    {
      "id": 1,
      "text": "How much of your time is occupied by obsessive thoughts?",
      "options": [
        "None",
        "Less than 1 hr/day or occasional occurrence",
        "1 to 3 hrs/day or frequent",
        "Greater than 3 and up to 8 hrs/day or very frequent occurrence",
        "Greater than 8 hrs/day or nearly constant occurrence"
      ]
    },
    {
      "id": 2,
      "text": "How much do your obsessive thoughts interfere with your work, school, social, or other important role functioning? Is there anything that you don’t do because of them?",
      "options": [
        "None",
        "Slight interference with social or other activities, but overall performance not impaired",
        "Definite interference with social or occupational performance, but still manageable",
        "Causes substantial impairment in social or occupational performance",
        "Incapacitating"
      ]
    },
    {
      "id": 3,
      "text": "How much distress do your obsessive thoughts cause you?",
      "options": [
        "None",
        "Not too disturbing",
        "Disturbing, but still manageable",
        "Very disturbing",
        "Near constant and disabling distress"
      ]
    },
    {
      "id": 4,
      "text": "How much of an effort do you make to resist the obsessive thoughts?",
      "options": [
        "Try to resist all the time",
        "Try to resist most of the time",
        "Make some effort to resist",
        "Yield to all obsessions without attempting to control them, but with some reluctance",
        "Completely and willingly yield to all obsessions"
      ]
    },
    {
      "id": 5,
      "text": "How much control do you have over your obsessive thoughts?",
      "options": [
        "Complete control",
        "Usually able to stop or divert obsessions with some effort and concentration",
        "Sometimes able to stop or divert obsessions",
        "Rarely successful in stopping or dismissing obsessions, can only divert attention with difficulty",
        "Obsessions are completely involuntary, rarely able to even momentarily alter obsessive thinking"
      ]
    },
    #The next several questions are about your compulsive behaviors. Compulsions are urges that people have to do something to lessen feelings of anxiety or other discomfort.  Often they do repetitive, purposeful, intentional behaviors called rituals. The behavior itself may seem appropriate but it becomes a ritual when done to excess.  Washing, checking, repeating, straightening, hoarding and many other behaviors can be rituals.  Some rituals are mental.  For example, thinking or saying things over and over under your breath.
    {
      "id": 6,
      "text": "How much time do you spend performing compulsive behaviors?",
      "options": [
        "None",
        "Less than 1 hr/day or occasional performance of compulsive behaviors",
        "From 1 to 3 hrs/day, or frequent performance of compulsive behaviors",
        "More than 3 and up to 8 hrs/day, or very frequent performance of compulsive behaviors",
        "More than 8 hrs/day, or near constant performance of compulsive behaviors (too numerous to count)"
      ]
    },
    {
      "id": 7,
      "text": "How much do your compulsive behaviors interfere with your work, school, social, or other important role functioning?",
      "options": [
        "None",
        "Slight interference with social or other activities, but overall performance not impaired",
        "Definite interference with social or occupational performance, but still manageable",
        "Causes substantial impairment in social or occupational performance",
        "Incapacitating"
      ]
    },
    {
      "id": 8,
      "text": "How would you feel if prevented from performing your compulsion(s)?",
      "options": [
        "None",
        "Only slightly anxious if compulsions prevented",
        "Anxiety would mount but remain manageable if compulsions prevented",
        "Prominent and very disturbing increase in anxiety if compulsions interrupted",
        "Incapacitating anxiety from any intervention aimed at modifying activity"
      ]
    },
    {
      "id": 9,
      "text": "How much of an effort do you make to resist the compulsions?",
      "options": [
        "Always try to resist",
        "Try to resist most of the time",
        "Make some effort to resist",
        "Yield to almost all compulsions without attempting to control them, but with some reluctance",
        "Completely and willingly yield to all compulsions"
      ]
    },
    {
      "id": 10,
      "text": "How strong is the drive to perform the compulsive behavior? How much control do you have over the compulsions?",
      "options": [
        "Complete control",
        "Pressure to perform the behavior but usually able to exercise voluntary control over it",
        "Strong pressure to perform behavior, can control it only with difficulty",
        "Very strong drive to perform behavior, must be carried to completion, can only delay with difficulty",
        "Drive to perform behavior experienced as completely involuntary and overpowering, rarely able to even momentarily delay activity"
      ]
    }
  ]
},
    "PCL-5": {
        "name": "PTSD Checklist for DSM-5 (PCL-5)",
        "testname":"PCL-5",
        "instructions":"Thinking about your most stressful experience, please select the option for each problem that describes how much it has bothered you in the past month.",
        "questions": [
            {"id": 1, "text": "Repeated, disturbing memories of the stressful experience", "options": ["Not at all", "A little bit", "Moderately", "Quite a bit", "Extremely"]},
            {"id": 2, "text": "Repeated, disturbing dreams of the stressful experience", "options": ["Not at all", "A little bit", "Moderately", "Quite a bit", "Extremely"]},
            {"id": 3, "text": "Suddenly feeling as if the stressful experience were happening again", "options": ["Not at all", "A little bit", "Moderately", "Quite a bit", "Extremely"]},
            {"id": 4, "text": "Feeling very upset when reminded of the stressful experience", "options": ["Not at all", "A little bit", "Moderately", "Quite a bit", "Extremely"]},
            {"id": 5, "text": "Strong physical reactions when reminded of the stressful experience", "options": ["Not at all", "A little bit", "Moderately", "Quite a bit", "Extremely"]},
            {"id": 6, "text": "Avoiding memories, thoughts, or feelings related to the stressful experience", "options": ["Not at all", "A little bit", "Moderately", "Quite a bit", "Extremely"]},
            {"id": 7, "text": "Avoiding external reminders of the stressful experience", "options": ["Not at all", "A little bit", "Moderately", "Quite a bit", "Extremely"]},
            {"id": 8, "text": "Trouble remembering important parts of the stressful experience", "options": ["Not at all", "A little bit", "Moderately", "Quite a bit", "Extremely"]},
            {"id": 9, "text": "Strong negative beliefs about yourself, others, or the world", "options": ["Not at all", "A little bit", "Moderately", "Quite a bit", "Extremely"]},
            {"id": 10, "text": "Blaming yourself or others for the stressful experience", "options": ["Not at all", "A little bit", "Moderately", "Quite a bit", "Extremely"]},
            {"id": 11, "text": "Strong negative feelings (fear, horror, anger, guilt, shame)", "options": ["Not at all", "A little bit", "Moderately", "Quite a bit", "Extremely"]},
            {"id": 12, "text": "Loss of interest in activities you used to enjoy", "options": ["Not at all", "A little bit", "Moderately", "Quite a bit", "Extremely"]},
            {"id": 13, "text": "Feeling distant or cut off from other people", "options": ["Not at all", "A little bit", "Moderately", "Quite a bit", "Extremely"]},
            {"id": 14, "text": "Trouble experiencing positive feelings", "options": ["Not at all", "A little bit", "Moderately", "Quite a bit", "Extremely"]},
            {"id": 15, "text": "Irritable behavior, angry outbursts, or acting aggressively", "options": ["Not at all", "A little bit", "Moderately", "Quite a bit", "Extremely"]},
            {"id": 16, "text": "Taking too many risks or doing things that could cause harm", "options": ["Not at all", "A little bit", "Moderately", "Quite a bit", "Extremely"]},
            {"id": 17, "text": "Being 'superalert', watchful, or on guard", "options": ["Not at all", "A little bit", "Moderately", "Quite a bit", "Extremely"]},
            {"id": 18, "text": "Feeling jumpy or easily startled", "options": ["Not at all", "A little bit", "Moderately", "Quite a bit", "Extremely"]},
            {"id": 19, "text": "Having difficulty concentrating", "options": ["Not at all", "A little bit", "Moderately", "Quite a bit", "Extremely"]},
            {"id": 20, "text": "Trouble falling or staying asleep", "options": ["Not at all", "A little bit", "Moderately", "Quite a bit", "Extremely"]}
        ]
    },
    "MSI-BPD": {
        "name": "MacLean Screening Instrument(MSI-BPD)",
        "testname":"MSI-BPD",
        "instructions":"Please answer the following questions to the best of your ability.",
        "questions": [
            {"id": 1, "text": "Have any of your closest relationships been troubled by a lot of arguments or repeated breakups?", "options": ["Yes", "No"]},
            {"id": 2, "text": "Have you deliberately hurt yourself physically or made a suicide attempt?", "options": ["Yes", "No"]},
            {"id": 3, "text": "Have you had at least two other problems with impulsivity?", "options": ["Yes", "No"]},
            {"id": 4, "text": "Have you been extremely moody?", "options": ["Yes", "No"]},
            {"id": 5, "text": "Have you felt very angry a lot of the time or often acted in an angry/sarcastic manner?", "options": ["Yes", "No"]},
            {"id": 6, "text": "Have you often been distrustful of other people?", "options": ["Yes", "No"]},
            {"id": 7, "text": "Have you frequently felt unreal or as if things around you were unreal?", "options": ["Yes", "No"]},
            {"id": 8, "text": "Have you chronically felt empty?", "options": ["Yes", "No"]},
            {"id": 9, "text": "Have you often felt that you had no idea of who you are or that you have no identity?", "options": ["Yes", "No"]},
            {"id": 10, "text": "Have you made desperate efforts to avoid feeling abandoned or being abandoned?", "options": ["Yes", "No"]}
        ]
    }
}


# 4. Define scoring functions
def score_phq9(responses):
    scores = [r['option_index'] for r in responses if r['question_id'] <= 9]
    total = sum(scores)

    # Interpretation mapping
    interpretations = {
        (0, 4): "minimal",
        (5, 9): "mild",
        (10, 14): "moderate",
        (15, 19): "moderately severe",
        (20, 27): "severe"
    }

    for (min_val, max_val), severity in interpretations.items():
        if min_val <= total <= max_val:
            interpretation = severity
            break

    # Patient summary
    summary = f"Your results suggest {interpretation} symptoms of depression. "
    if total >= 10:
        summary += "This indicates you may benefit from professional support. "
    summary += "Please consult a healthcare provider for a complete evaluation."

    # Detailed report
    details = {
        "score": total,
        "interpretation": f"{interpretation.capitalize()} depression",
        "risk_flags": [],
        "clinical_notes": []
    }

    # Suicide risk flag
    if len(responses) > 8 and responses[8]['option_index'] >= 1:
        details["risk_flags"].append("suicidal_ideation")
        summary += " Important: Your responses indicate thoughts about self-harm - please seek immediate support."

    return {
        "patient_summary": summary,
        "detailed_report": details
    }

def score_gad7(responses):
    scores = [r['option_index'] for r in responses[:7]]
    total = sum(scores)

    # Interpretation
    if total <= 4:
        interpretation = "minimal"
    elif total <= 9:
        interpretation = "mild"
    elif total <= 14:
        interpretation = "moderate"
    else:
        interpretation = "severe"

    summary = f"Your results indicate {interpretation} anxiety symptoms. "
    if total >= 10:
        summary += "This level of anxiety often benefits from professional support. "
    summary += "Consult a healthcare provider for personalized advice."

    return {
        "patient_summary": summary,
        "detailed_report": {
            "score": total,
            "interpretation": f"{interpretation.capitalize()} anxiety",
            "risk_flags": [],
            "clinical_notes": []
        }
    }

def score_asrs(responses):
    part_a = sum(r['option_index'] for r in responses[:6])
    part_b = sum(r['option_index'] for r in responses[6:18])
    total = part_a + part_b

    # Patient summary
    if part_a >= 14:
        summary = "Your responses strongly suggest ADHD symptoms. "
    elif part_a >= 10:
        summary = "Your responses indicate possible ADHD symptoms. "
    else:
        summary = "Your responses show minimal ADHD symptoms. "

    summary += "ADHD diagnosis requires professional evaluation - please consult a specialist."

    # Detailed report
    details = {
        "part_a_score": part_a,
        "part_b_score": part_b,
        "score": total,
        "interpretation": "",
        "risk_flags": [],
        "clinical_notes": ["Part A ≥14 suggests ADHD diagnostic consistency"]
    }

    if part_a >= 14:
        details["interpretation"] = "Consistent with ADHD diagnosis"
        details["risk_flags"].append("adhd_high_risk")
    else:
        details["interpretation"] = "Insufficient evidence for ADHD diagnosis"

    return {
        "patient_summary": summary,
        "detailed_report": details
    }

def score_aq10(responses):
    agree_points = [1, 7, 8, 10]
    disagree_points = [2, 3, 4, 5, 6, 9]

    total = 0
    for r in responses:
        qid = r['question_id']
        option_idx = r['option_index']

        if qid in agree_points:
            total += 1 if option_idx in [0, 1] else 0
        elif qid in disagree_points:
            total += 1 if option_idx in [2, 3] else 0

    interpretation = (
        "May benefit from full diagnostic assessment"
        if total >= 6 else
        "Unlikely to need assessment"
    )

    summary = (
        f"Your score is {total}/10 on the AQ-10 questionnaire. "
        f"{interpretation}. Please consult a healthcare professional for further evaluation."
    )

    return {
        "patient_summary": summary,
        "detailed_report": {
            "score": total,
            "interpretation": interpretation,
            "risk_flags": ["possible_autism"] if total >= 6 else [],
            "clinical_notes": []
        }
    }

def score_dast(responses):
    # Reverse scoring questions
    reverse_questions = [4, 5, 7]

    total = 0
    for r in responses:
        qid = r['question_id']
        option_idx = r['option_index']

        # Yes=0, No=1 in options
        if qid in reverse_questions:
            # Reverse score: NO = 1 point
            total += 1 if option_idx == 1 else 0
        else:
            # Normal score: YES = 1 point
            total += 1 if option_idx == 0 else 0

    # Interpretation
    levels = {
        (0, 0): "no problems",
        (1, 5): "low level",
        (6, 10): "moderate level (likely abuse)",
        (11, 15): "substantial level",
        (16, 20): "severe level"
    }

    # Patient summary
    for (min_val, max_val), level in levels.items():
        if min_val <= total <= max_val:
            summary = f"Your screening shows {level} of drug-related concerns. "
            break

    summary += "Substance use can significantly impact health - consider speaking with a counselor."

    return {
        "patient_summary": summary,
        "detailed_report": {
            "score": total,
            "interpretation": level,
            "risk_flags": ["substance_abuse"] if total >= 6 else [],
            "clinical_notes": []}}

def score_audit(responses):
    total = 0
    for i, r in enumerate(responses):
        qid = r['question_id']
        option_idx = r['option_index']

        if qid <= 8:  # Questions 1-8
            total += option_idx
        else:  # Questions 9-10
            # Map: 0→0, 1→2, 2→4
            total += 0 if option_idx == 0 else (2 if option_idx == 1 else 4)

    # Interpretation
    if total == 0:
        interpretation = "abstainer"
    elif total <= 7:
        interpretation = "low-risk"
    elif total <= 14:
        interpretation = "hazardous or harmful use"
    else:
        interpretation = "likely alcohol dependence"

    summary = f"Your alcohol use patterns indicate {interpretation}. "
    if total >= 8:
        summary += "This level of drinking may affect your health. Consider discussing with a doctor."

    return {
        "patient_summary": summary,
        "detailed_report": {
            "score": total,
            "interpretation": interpretation,
            "risk_flags": ["alcohol_concern"] if total >= 8 else [],
            "clinical_notes": []
        }
    }

def score_ybocs(responses):
    total = sum(r['option_index'] for r in responses)

    if total <= 7: interpretation = "Subclinical"
    elif total <= 15: interpretation = "Mild"
    elif total <= 23: interpretation = "Moderate"
    elif total <= 31: interpretation = "Severe"
    else: interpretation = "Extreme"

    summary = (
        f"Your score is {total}/40 on the Y-BOCS scale. "
        f"This indicates {interpretation} obsessive-compulsive symptoms."
    )

    return {
        "patient_summary": summary,
        "detailed_report": {
            "score": total,
            "interpretation": interpretation,
            "risk_flags": ["ocd_high_risk"] if total >= 24 else [],
            "clinical_notes": []
        }
    }

def score_pcl5(responses):
    total = sum(r['option_index'] for r in responses)

    cluster_b = any(r['option_index'] >= 2 for r in responses[:5])
    cluster_c = any(r['option_index'] >= 2 for r in responses[5:7])
    cluster_d = sum(1 for r in responses[7:14] if r['option_index'] >= 2) >= 2
    cluster_e = sum(1 for r in responses[14:] if r['option_index'] >= 2) >= 2

    probable_ptsd = cluster_b and cluster_c and cluster_d and cluster_e

    interpretation = (
        "Probable PTSD (clinical interview recommended)"
        if probable_ptsd or total >= 31 else
        "Unlikely PTSD"
    )

    summary = (
        f"Your score is {total}/80 on the PCL-5 PTSD scale. "
        f"{interpretation}."
    )

    return {
        "patient_summary": summary,
        "detailed_report": {
            "score": total,
            "interpretation": interpretation,
            "risk_flags": ["ptsd_high_risk"] if probable_ptsd else [],
            "clinical_notes": []
        }
    }

def score_mdq(responses):
    symptom_count = sum(1 for r in responses[:13] if r['option_index'] == 0)  
    co_occurrence = responses[13]['option_index'] == 0  
    problem_severity = responses[14]['option_index'] >= 2  

    interpretation = (
        "Positive screen for bipolar disorder"
        if symptom_count >= 7 and co_occurrence and problem_severity
        else "Negative screen"
    )

    total = symptom_count  # MDQ doesn't have max score like others

    summary = (
        f"Your score is {total}/13 on the MDQ symptom checklist. "
        f"{interpretation}."
    )

    return {
        "patient_summary": summary,
        "detailed_report": {
            "score": total,
            "interpretation": interpretation,
            "risk_flags": ["bipolar_high_risk"] if interpretation.startswith("Positive") else [],
            "clinical_notes": []
        }
    }

def score_eat26(responses):
    score_map = {0: 3, 1: 2, 2: 1, 3: 0, 4: 0, 5: 0}

    total = 0
    for r in responses[:26]:
        if r['question_id'] == 26:
            total += 3 - score_map.get(r['option_index'], 0)
        else:
            total += score_map.get(r['option_index'], 0)

    behavioral_flags = []
    for r in responses[26:]:
        if r['option_index'] > 0:
            behavioral_flags.append(f"Behavior {r['question_id']-26} reported")

    interpretation = (
        "High risk of eating disorder" if total >= 20
        else "Possible risk" if total >= 11
        else "Low risk"
    )

    summary = (
        f"Your score is {total}/78 on the EAT-26 eating attitudes scale. "
        f"{interpretation}."
    )

    return {
        "patient_summary": summary,
        "detailed_report": {
            "score": total,
            "interpretation": interpretation,
            "risk_flags": ["eating_disorder_high_risk"] if total >= 20 else [],
            "clinical_notes": behavioral_flags
        }
    }


def score_bpd(responses):
    total = sum(1 for r in responses if r['option_index'] == 0)

    interpretation = (
        "Likely BPD" if total >= 7
        else "Borderline range" if total >= 5
        else "Unlikely BPD"
    )

    summary = (
        f"Your score is {total}/10 on the MSI-BPD scale. "
        f"{interpretation}."
    )

    return {
        "patient_summary": summary,
        "detailed_report": {
            "score": total,
            "interpretation": interpretation,
            "risk_flags": ["bpd_high_risk"] if total >= 7 else [],
            "clinical_notes": []
        }
    }

# 5. Create SCORING_FUNCTIONS dictionary
SCORING_FUNCTIONS = {
    "PHQ-9": score_phq9,
    "GAD-7": score_gad7,
    "AQ-10": score_aq10,
    "DAST": score_dast,
    "AUDIT": score_audit,
    "Y-BOCS": score_ybocs,
    "PCL-5": score_pcl5,
    "Mood Disorder Questionnaire": score_mdq,
    "EAT-26": score_eat26,
    "MSI-BPD": score_bpd,
    "ASRS": score_asrs
}

def normalize_string(s: str) -> str:
    return re.sub(r'[^A-Za-z]+', '', s).lower()


# ----------------------------
# Questionnaire
# ----------------------------
def get_questionnaire_service(disorder_name: str):
    normalized = normalize_string(disorder_name)

    if normalized not in DISORDER_MAPPING:
        raise HTTPException(404, "Disorder not found")

    key = DISORDER_MAPPING[normalized]

    if key not in QUESTIONNAIRES:
        raise HTTPException(501, "Not implemented")

    return QUESTIONNAIRES[key]


# ----------------------------
# Evaluation
# ----------------------------
def evaluate_service(db: Session, request, user=None, session_id=None, meta=None):
    normalized = normalize_string(request.questionnaire)

    questionnaire_key = None
    for _, q_key in DISORDER_MAPPING.items():
        if normalize_string(q_key) == normalized:
            questionnaire_key = q_key
            break

    if not questionnaire_key:
        raise HTTPException(404, "Questionnaire not found")

    scoring_fn = SCORING_FUNCTIONS[questionnaire_key]

    result = scoring_fn([r.dict() for r in request.responses])

    # Save submission
    submission = AssessmentSubmission(
        user_id=getattr(user, "id", None),
        session_id=session_id,
        assessment_id=questionnaire_key,
        score=result["detailed_report"].get("score"),
        result_json=result,
        ip_address=meta.get("ip") if meta else None,
        user_agent=meta.get("agent") if meta else None,
    )

    db.add(submission)

    # Log raw event
    event = RawEvent(
        user_id=getattr(user, "id", None),
        session_id=session_id,
        event_type="ASSESSMENT_SUBMITTED",
        payload={"request": request.dict(), "result": result}
    )

    db.add(event)

    db.commit()

    return result