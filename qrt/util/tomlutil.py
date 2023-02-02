import datetime
import tomllib
from typing import Dict, Union, List, Tuple

from qrt.util.questionnaire import Questionnaire, Page, Question, ZofarQuestionMCMatrix, AnswerOption, SCAnswerOption, \
    SCMatrixItem, SCResponseDomain, VarRef, Variable, VAR_TYPE_SC, HeaderQuestion, ZofarAttachedOpen, VAR_TYPE_STR, \
    MatrixResponseDomain, ZofarPageObject, HeaderTitle, HeaderInstruction, HeaderIntroduction


def read_pv(input_str: str) -> Questionnaire:
    pv_dict = tomllib.loads(input_str)
    survey = pv_dict.pop('survey')
    pages = sorted(list({q_data['page'] for q_id, q_data in pv_dict.items()}))
    q = Questionnaire()
    for page in pages:
        p = Page(uid=page)
        page_questions = {q_uid: q_data for q_uid, q_data in pv_dict.items() if q_data['page'] == page}
        for q_id, q_data in page_questions.items():
            if q_data['type'] == 'matrixQuestionSingleChoice':
                p.body_questions.append(toml_parse_mqsc(q_id, q_data))
                pass
            elif q_data['type'] == 'questionsSingleChoice':
                pass
            elif q_data['type'] == 'multipleChoice':
                pass
            elif q_data['type'] == 'matrixMultipleChoice':
                pass
            elif q_data['type'] == 'questionOpen':
                pass
            elif q_data['type'] == 'monthpicker':
                pass
            elif q_data['type'] == 'openMatrix':
                pass
        pass
    pass


def ao_list_to_header_list(ao_list: List[AnswerOption]) -> Tuple[List[ZofarPageObject], List[ZofarPageObject]]:
    reg_header = [HeaderTitle(uid=ao.uid, content=ao.label) for ao in ao_list if not ao.missing]
    mis_header = [HeaderTitle(uid=ao.uid, content=ao.label) for ao in ao_list if ao.missing]
    return reg_header, mis_header


def toml_parse_mqsc(q_uid: str,
                    q_data: Dict[str, Union[int, float, str, dict, list, datetime.datetime, bool]]) -> Question:
    ao_list = [SCAnswerOption(**ao) for ao in q_data['aos']]
    it_list = []
    q_header_list = []
    for header in q_data['headers']:
        assert isinstance(header, dict)
        if header['type'] == 'question':
            q_header_list.append(HeaderQuestion(uid=header['uid'], content=header['text']))
        elif header['type'] == 'instruction':
            q_header_list.append(HeaderInstruction(uid=header['uid'], content=header['text']))
        elif header['type'] == 'introduction':
            q_header_list.append(HeaderIntroduction(uid=header['uid'], content=header['text']))

    for item in q_data['items']:
        assert isinstance(item, dict)
        var_ref = VarRef(variable=Variable(name=item['variable'], type=VAR_TYPE_SC))
        rd = SCResponseDomain(ao_list=ao_list, var_ref=var_ref)
        header_list = [HeaderQuestion(uid='q', content=item['text'])]
        att_open_list = []
        if 'attachedOpen' in item.keys():
            prefix = None
            postfix = None
            for att_open_raw in item['attachedOpen']:
                att_open_var_ref = VarRef(variable=Variable(name=att_open_raw['variable'], type=VAR_TYPE_STR))
                if 'prefix' in att_open_raw:
                    if att_open_raw['prefix'] != {}:
                        prefix = att_open_raw['prefix']
                if 'postfix' in att_open_raw:
                    if att_open_raw['postfix'] != {}:
                        postfix = att_open_raw['postfix']
                att_open_list.append(ZofarAttachedOpen(uid='att_open_list',
                                                       var_ref=att_open_var_ref,
                                                       prefix=prefix,
                                                       postfix=postfix))

        it_list.append(SCMatrixItem(uid=item['uid'], header_list=header_list,
                                    response_domain=rd,
                                    attached_open_list=att_open_list))

    rd = MatrixResponseDomain(no_response_options=str(len(ao_list)), item_list=it_list)
    title_header, missing_header = ao_list_to_header_list(ao_list)
    q = ZofarQuestionMCMatrix(type='matrixQuestionSingleChoice', uid=q_uid, response_domain=rd,
                              title_header=title_header, missing_header=missing_header,
                              header_list=q_header_list)
    return q
