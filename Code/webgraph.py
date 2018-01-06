#!/usr/bin/python3
 
# Author: J. Saarloos
# v0.7.1	15-08-2017

"""
Make an HTML graph.
"""

from datetime import datetime
import logging
import sqlite3


class webgraph(object):

	db = None
	pageName = ""
	min = []
	avg = []
	max = []
	records = 0
	querystart = 0.0
	names = []
	queryEnd = 0.0
	data = None
	htmlFile = ""
	selection = []


	def __init__(self, db):
		
		self.db = db
		for f in self.db.fields:
			self.names.append(f[0].lower())
		self.htmlFile = self.db.dbfolder + "graph.html"
		self.pageName = "Raspberry Pi Data Logger"

	def makeGraph(self, start, end = None, names = None):

		self.querystart = start
		if (end is None):
			self.queryEnd = 0.0
		else:
			self.queryEnd = end
		if (names is None):
			names = self.names
		for i, n in enumerate(self.names):
			if (n in names):
				self.selection.append(i)
				self.min.append(5000.0)
				self.avg.append(0.0)
				self.max.append(0.0)
		
		print("Starting graph.")
		html = ""
		html += ("<html>\n")
		html += ("\t<head>\n")
		html += ("\t\t<title>{0}</title>\n".format(self.pageName))
		html += self.print_graph_script()
		html += ("\t</head>\n")
		html += ("\t<body>\n")
		html += ("\t\t<h1>{0}</h1>\n".format(self.pageName))
		html += ("\t\t<hr>")
		html += self.show_graph()
		html += self.show_stats()
		html += ("\t</body>\n")
		html += ("</html>")
		msg = ""

		try:
			with open(self.htmlFile, "wb") as text_file:
				print("writing to file")
				text_file.write(bytes(html, "utf-8"))
				msg = None
		except FileNotFoundError:
			logging.debug("File not found: " + self.htmlFile)
			msg = ("File not found. Unable to make graph.")
		except IOError:
			logging.debug("IO error trying to write to file: " + self.htmlFile)
			msg = ("IO error. Unable to make graph.")
		except:
			msg = "Unknown error writing to file."
		finally:
			self.data = None
			self.min = []
			self.avg = []
			self.max = []
			self.records = 0
			self.selection = []
			return(html)
	
	def print_graph_script(self):
		# google chart snippet
		chart_code="""
		<script type="text/javascript" src="https://www.google.com/jsapi"></script>
		<script type="text/javascript">
			google.load("visualization", "1", {packages:["corechart"]});
			google.setOnLoadCallback(drawChart);
			function drawChart() {
				var data = google.visualization.arrayToDataTable([
				"""
		chart_code += "['Time'"
		print(self.selection)
		for i in self.selection:
			chart_code += ", '{}'".format(self.names[i])
		print(self.selection)
		chart_code += "],\n"
		chart_code += self.format_table()
		chart_code += """
				]);

			var options = {
				title: '"""
		chart_code += self.pageName
		chart_code += """'
			};

			var chart = new google.visualization.LineChart(document.getElementById('chart_div'));
			chart.draw(data, options);
		}
		</script>\n"""

		return(chart_code)
	
	def show_graph(self):
		text = ("<h2>Temperature Chart</h2>")
		text +=('<div id="chart_div" style="width: 1680; height: 880;"></div>')
		return(text)
	
	def show_stats(self):
		text = ("<hr>\n")
		text += ("<center>\n")
		text += ("\n")
		text += "<TABLE border = '0' WIDTH='{0}'><TH COLSPAN='{1}'><h2>Summary: </h2>({2} records)</TH>\n".format(str(120 + len(self.selection) * 100), str(len(self.selection) + 1), str(self.records))
		text += "<TR><TD ALIGN = 'center'><H2>Channels:</H2></TD>"
		for i in self.selection:
			text += "<TD ALIGN = 'center'><H2>{}</H2></TD>".format(self.names[i])
		text += "</TR>\n"
		text += "<TR><TD ALIGN = 'center'><H2>Minimum:</H2></TD>{}</TR>\n".format(self.formatForStats(self.min))
		text += "<TR><TD ALIGN = 'center'><H2>Average:</H2></TD>{}</TR>\n".format(self.formatForStats(self.avg))
		text += "<TR><TD ALIGN = 'center'><H2>Maximum:</H2></TD>{}</TR>\n".format(self.formatForStats(self.max))
		text += "</TABLE>"
		text += ("</center>\n")
		text += ("<hr>\n")
		text += ("<hr>\n")
		return(text)

	def formatForStats(self, table):

		msg = ""
		for i, t in zip(self.selection, table):
			type = self.db.fields[i][1]
			if ((type == "light") or (type == "mst")):
				msg += "<TD ALIGN = 'center'><h3>{0} ({1})</h3></TD>".format(str(t), self.perc(t))
			else:
				msg += "<TD ALIGN = 'center'><h3>{0}</h3></TD>".format(str(t))
		return(msg)
	
	def get_mma(self, data):
		"""Display a graph of min, avg and max of 1 channel."""

		return(min, max, avg)

	def format_table(self):
		"""Returns a formatted table of the graph data and calculates min, avg and max values per data type."""

		chart_table = ""
		rows = self.db.display_data(self.querystart, self.queryEnd, raw = True)
		for row in rows:
			try:
				chart_table += "\t\t\t\t['{0}'{1}],\n".format(str(datetime.fromtimestamp(int(row[0])).strftime("%Y-%m-%d %H:%M:%S")), self.formatRow(row[1:]))
			except fieldException as txt:
				return(txt)

			for i, j in enumerate(self.selection):
				j += 1
				self.avg[i] += row[j]
				if (row[j] < self.min[i]):
					self.min[i] = row[j]
				if (row[j] > self.max[i]):
					self.max[i] = row[j]

		for i in range(len(self.avg)):
			self.avg[i] = round(self.avg[i] / len(rows), 1)
		self.records = len(rows)
		return(chart_table[::][:-1])
	
	def formatRow(self, row):
		""""""

		if (len(row) <= len(self.names)):
			data = ""
			for i in self.selection:
				type = self.db.fields[i][1]
				if ((type == "light") or (type == "mst")):
					data += (", " + self.perc(row[i]))
				else:
					data += (", " + str(row[i]))
			return(data)
		else:
			raise fieldException("Incorrect amount of datafields.")

	def perc(self, number):

		return(str(round((number / self.db.adc.bits * 100), 2)))
	
class fieldException(Exception):
	pass