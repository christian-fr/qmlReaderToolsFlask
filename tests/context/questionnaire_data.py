import re

mqsc_example_str = """<zofar:matrixQuestionSingleChoice xmlns:zofar="http://www.his.de/zofar/xml/questionnaire" uid="mqsc1" block="true">
				<zofar:header>
					<zofar:introduction uid="intro1" visible="!missingStartDate.value and !missingEndDate.value and zofar.getJsonProperty(episodeObj,'name')!=''" block="true">Wir beziehen uns hier auf Ihr Praktikum "#{zofar.getJsonProperty(episodeObj,'name')}" zwischen #{zofar.labelOf(startmonth)} #{zofar.labelOf(startyear)} und #{zofar.labelOf(endmonth)} #{zofar.labelOf(endyear)}.</zofar:introduction>
					<zofar:introduction uid="intro2" visible="!missingStartDate.value and !missingEndDate.value and zofar.getJsonProperty(episodeObj,'name')==''" block="true">Wir beziehen uns hier auf Ihr Praktikum zwischen #{zofar.labelOf(startmonth)} #{zofar.labelOf(startyear)} und #{zofar.labelOf(endmonth)} #{zofar.labelOf(endyear)}.</zofar:introduction>
					<zofar:introduction uid="intro3" visible="(missingStartDate.value or missingEndDate.value) and zofar.getJsonProperty(episodeObj,'name')!=''" block="true">Wir beziehen uns hier auf Ihr Praktikum "#{zofar.getJsonProperty(episodeObj,'name')}".</zofar:introduction>
					<zofar:question uid="q" visible="true" block="true">Bitte geben Sie für jede Aussage an, ob sie auf dieses Praktikum völlig zutrifft, eher zutrifft, teilweise zutrifft, eher nicht zutrifft oder gar nicht zutrifft.</zofar:question>
				</zofar:header>
				<zofar:responseDomain uid="rd" noResponseOptions="6">
					<zofar:header>
						<zofar:title uid="ti1">trifft v&#246;llig zu</zofar:title>
						<zofar:title uid="ti2">trifft eher zu</zofar:title>
						<zofar:title uid="ti3">teils/teils</zofar:title>
						<zofar:title uid="ti4">trifft eher nicht zu</zofar:title>
						<zofar:title uid="ti5">trifft gar nicht zu</zofar:title>
					</zofar:header>
					<zofar:missingHeader>
						<zofar:title uid="ti6">wei&#223; nicht</zofar:title>
					</zofar:missingHeader>
					<zofar:item uid="it1" visible="((zofar.asNumber(endyear) * 100) + zofar.asNumber(endmonth)) lt zofar.asNumber(h_exitdatum)">
						<zofar:header>
							<zofar:question uid="q1" visible="true" block="true">Ich konnte bei diesem Praktikum immer wieder Neues dazulernen.</zofar:question>
						</zofar:header>
						<zofar:responseDomain itemClasses="true" variable="int021" itemClasses="true" uid="rd">
							<zofar:answerOption uid="ao1" label="trifft v&#246;llig zu" visible="true" value="1"/>
							<zofar:answerOption uid="ao2" label="trifft eher zu" visible="true" value="2"/>
							<zofar:answerOption uid="ao3" label="teils/teils" visible="true" value="3"/>
							<zofar:answerOption uid="ao4" label="trifft eher nicht zu" visible="true" value="4"/>
							<zofar:answerOption uid="ao5" label="trifft gar nicht zu" visible="true" value="5"/>
							<zofar:answerOption uid="ao6" label="wei&#223; nicht" visible="true" value="-9" missing="true" />
						</zofar:responseDomain>
					</zofar:item>
					<zofar:item uid="it1_1" visible="((zofar.asNumber(endyear) * 100) + zofar.asNumber(endmonth)) ge zofar.asNumber(h_exitdatum)">
						<zofar:header>
							<zofar:question uid="q2">Ich kann bei diesem Praktikum immer wieder Neues dazulernen.</zofar:question>
						</zofar:header>
						<zofar:responseDomain itemClasses="true" uid="rd" variable="int021">
							<zofar:answerOption uid="ao1" label="trifft v&#246;llig zu" visible="true" value="1"/>
							<zofar:answerOption uid="ao2" label="trifft eher zu" visible="true" value="2"/>
							<zofar:answerOption uid="ao3" label="teils/teils" visible="true" value="3"/>
							<zofar:answerOption uid="ao4" label="trifft eher nicht zu" visible="true" value="4"/>
							<zofar:answerOption uid="ao5" label="trifft gar nicht zu" visible="true" value="5"/>
							<zofar:answerOption uid="ao6" label="wei&#223; nicht" visible="true" value="-9" missing="true" />
						</zofar:responseDomain>
					</zofar:item>
					<zofar:item uid="it2" visible="((zofar.asNumber(endyear) * 100) + zofar.asNumber(endmonth)) lt zofar.asNumber(h_exitdatum)">
						<zofar:header>
							<zofar:question uid="q1">Die Betreuung durch die Einrichtung, in der ich das Praktikum absolviert habe, war sehr gut.</zofar:question>
						</zofar:header>
						<zofar:responseDomain itemClasses="true" uid="rd" variable="int022">
							<zofar:answerOption uid="ao1" label="trifft v&#246;llig zu" visible="true" value="1"/>
							<zofar:answerOption uid="ao2" label="trifft eher zu" visible="true" value="2"/>
							<zofar:answerOption uid="ao3" label="teils/teils" visible="true" value="3"/>
							<zofar:answerOption uid="ao4" label="trifft eher nicht zu" visible="true" value="4"/>
							<zofar:answerOption uid="ao5" label="trifft gar nicht zu" visible="true" value="5"/>
							<zofar:answerOption uid="ao6" label="wei&#223; nicht" visible="true" value="-9" missing="true" />
						</zofar:responseDomain>
					</zofar:item>
					<zofar:item uid="it2_2" visible="((zofar.asNumber(endyear) * 100) + zofar.asNumber(endmonth)) ge zofar.asNumber(h_exitdatum)">
						<zofar:header>
							<zofar:question uid="q2">Die Betreuung durch die Einrichtung, in der ich das Praktikum absolviere, ist sehr gut.</zofar:question>
						</zofar:header>
						<zofar:responseDomain variable="int022" itemClasses="true" uid="rd">
							<zofar:answerOption uid="ao1" label="trifft v&#246;llig zu" visible="true" value="1"/>
							<zofar:answerOption uid="ao2" label="trifft eher zu" visible="true" value="2"/>
							<zofar:answerOption uid="ao3" label="teils/teils" visible="true" value="3"/>
							<zofar:answerOption uid="ao4" label="trifft eher nicht zu" visible="true" value="4"/>
							<zofar:answerOption uid="ao5" label="trifft gar nicht zu" visible="true" value="5"/>
							<zofar:answerOption uid="ao6" label="wei&#223; nicht" visible="true" value="-9" missing="true" />
						</zofar:responseDomain>
					</zofar:item>
				</zofar:responseDomain>
			</zofar:matrixQuestionSingleChoice>"""
