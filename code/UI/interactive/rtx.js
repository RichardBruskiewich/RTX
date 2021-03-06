var input_qg = { "edges": [], "nodes": [] };
var qgids = [];
var cyobj = [];
var cytodata = [];
var predicates = {};
var message_id = null;
var summary_table_html = '';
var summary_tsv = [];
var columnlist = [];
var UIstate = {};

var baseAPI = "";
//var baseAPI = "http://localhost:5001/devED/";

function main() {
    get_example_questions();
    load_nodes_and_predicates();
    display_list('A');
    display_list('B');
    add_status_divs();
    cytodata[999] = 'dummy';
    UIstate.nodedd = 1;

    message_id = getQueryVariable("m") || null;
    if (message_id) {
	var statusdiv = document.getElementById("statusdiv");
	statusdiv.innerHTML = '';
	statusdiv.appendChild(document.createTextNode("You have requested ARAX message id = " + message_id));;
	statusdiv.appendChild(document.createElement("br"));

	document.getElementById("devdiv").innerHTML =  "Requested ARAX message id = " + message_id + "<br>";
	retrieve_message();
	openSection(null,'queryDiv');
    }
    else {
	openSection(null,'queryDiv');
	add_cyto();
   }
}

function sesame(head,content) {
    if (head == "openmax") {
	content.style.maxHeight = content.scrollHeight + "px";
	return;
    }
    else if (head == "collapse") {
        content.style.maxHeight = null;
	return;
    }
    else if (head) {
	head.classList.toggle("openaccordion");
    }

    if (content.style.maxHeight) {
	content.style.maxHeight = null;
    }
    else {
	content.style.maxHeight = content.scrollHeight + "px";
    }
}


function openSection(obj, sect) {
    if (obj != null) {
	var e = document.getElementsByClassName("menucurrent");
	e[0].className = "menuleftitem";
	obj.className = "menucurrent";
    }

    for (var e of document.getElementsByClassName("pagesection")) {
        e.style.maxHeight = null;
        e.style.visibility = 'hidden';
    }
    document.getElementById(sect).style.maxHeight = "none";
    document.getElementById(sect).style.visibility = 'visible';
    window.scrollTo(0,0);
}

// somehow merge with above?  eh...
function selectInput (obj, input_id) {
    var e = document.getElementsByClassName("slink_on");
    if (e[0]) { e[0].classList.remove("slink_on"); }
    obj.classList.add("slink_on");

    for (var s of ['qtext_input','qgraph_input','qjson_input','qdsl_input']) {
	document.getElementById(s).style.maxHeight = null;
	document.getElementById(s).style.visibility = 'hidden';
    }
    document.getElementById(input_id).style.maxHeight = "100%";
    document.getElementById(input_id).style.visibility = 'visible';
}


function clearJSON() {
    document.getElementById("jsonText").value = '';
}
function clearDSL() {
    document.getElementById("dslText").value = '';
}

function pasteQuestion(question) {
    document.getElementById("questionForm").elements["questionText"].value = question;
    document.getElementById("qqq").value = '';
    document.getElementById("qqq").blur();
}
function pasteExample(type) {
    if (type == "DSL") {
	document.getElementById("dslText").value = 'add_qnode(name=acetaminophen, id=n0)\nadd_qnode(type=protein, id=n1)\nadd_qedge(source_id=n0, target_id=n1, id=e0)\nexpand(edge_id=e0)\noverlay(action=compute_ngd, virtual_relation_label=N1, source_qnode_id=n0, target_qnode_id=n1)\nresultify()';
    }
    else {
	document.getElementById("jsonText").value = '{\n   "edges": [\n      {\n         "id": "qg2",\n         "source_id": "qg1",\n         "target_id": "qg0"\n      }\n   ],\n   "nodes": [\n      {\n         "id": "qg0",\n         "curie": "CHEMBL.COMPOUND:CHEMBL112"\n      },\n      {\n         "id": "qg1",\n         "type": "protein"\n      }\n   ]\n}';
    }
}

function reset_vars() {
    add_status_divs();
    document.getElementById("result_container").innerHTML = "";
    if (cyobj[0]) {cyobj[0].elements().remove();}
    document.getElementById("summary_container").innerHTML = "";
    document.getElementById("menunummessages").innerHTML = "--";
    document.getElementById("menunummessages").className = "numold menunum";
    document.getElementById("menunumresults").innerHTML = "--";
    document.getElementById("menunumresults").className = "numold menunum";
    summary_table_html = '';
    summary_tsv = [];
    cyobj = [];
    cytodata = [];
    UIstate.nodedd = 1;
}


// use fetch and stream
function postQuery(qtype) {
    var queryObj= {};
    queryObj.asynchronous = "stream";

    reset_vars();
    var statusdiv = document.getElementById("statusdiv");

    // assemble QueryObject
    if (qtype == "DSL") {
	document.getElementById("questionForm").elements["questionText"].value = '-- posted async query via DSL input --';
	statusdiv.innerHTML = "Posting DSL.  Looking for answer...";
	statusdiv.appendChild(document.createElement("br"));

	var dslArrayOfLines = document.getElementById("dslText").value.split("\n");
	queryObj["previous_message_processing_plan"] = { "processing_actions": dslArrayOfLines};
    }
    else if (qtype == "JSON") {
	document.getElementById("questionForm").elements["questionText"].value = '-- posted async query via direct JSON input --';
	statusdiv.innerHTML = "Posting JSON.  Looking for answer...";
	statusdiv.appendChild(document.createElement("br"));

        var jsonInput;
	try {
	    jsonInput = JSON.parse(document.getElementById("jsonText").value);
	}
	catch(e) {
            statusdiv.appendChild(document.createElement("br"));
	    if (e.name == "SyntaxError")
		statusdiv.innerHTML += "<b>Error</b> parsing JSON input. Please correct errors and resubmit: ";
	    else
		statusdiv.innerHTML += "<b>Error</b> processing input. Please correct errors and resubmit: ";
            statusdiv.appendChild(document.createElement("br"));
	    statusdiv.innerHTML += "<span class='error'>"+e+"</span>";
	    return;
	}
	queryObj.message = { "query_graph" :jsonInput };
	queryObj.max_results = 100;

	clear_qg();
    }
    else {  // qGraph
	document.getElementById("questionForm").elements["questionText"].value = '-- posted async query via graph --';
	statusdiv.innerHTML = "Posting graph.  Looking for answer...";
        statusdiv.appendChild(document.createElement("br"));

	// ids need to start with a non-numeric character
	for (var gnode of input_qg.nodes) {
	    if (String(gnode.id).match(/^\d/))
		gnode.id = "qg" + gnode.id;

	    if (gnode.is_set) {
		var list = gnode.name.split("LIST_")[1];
		gnode.curie = get_list_as_curie_array(list);
	    }
	}
	for (var gedge of input_qg.edges) {
	    if (String(gedge.id).match(/^\d/))
		gedge.id = "qg" + gedge.id;
	    if (String(gedge.source_id).match(/^\d/))
		gedge.source_id = "qg" + gedge.source_id;
	    if (String(gedge.target_id).match(/^\d/))
		gedge.target_id = "qg" + gedge.target_id;

	}

	document.getElementById('qg_form').style.visibility = 'hidden';
	document.getElementById('qg_form').style.maxHeight = null;

	queryObj.message = { "query_graph" :input_qg };
	//queryObj.bypass_cache = bypass_cache;
	queryObj.max_results = 100;

	document.getElementById("jsonText").value = JSON.stringify(input_qg,null,2);
	clear_qg();
    }

    var cmddiv = document.createElement("div");
    cmddiv.id = "cmdoutput";
    statusdiv.appendChild(cmddiv);
//    statusdiv.appendChild(document.createElement("br"));

    statusdiv.appendChild(document.createTextNode("Processing step "));
    var span = document.createElement("span");
    span.id = "finishedSteps";
    span.style.fontWeight= "bold";
//    span.className = "menunum numnew";
    span.appendChild(document.createTextNode("0"));
    statusdiv.appendChild(span);
    statusdiv.appendChild(document.createTextNode(" of "));
    span = document.createElement("span");
    span.id = "totalSteps";
//    span.className = "menunum";
    span.appendChild(document.createTextNode("??"));
    statusdiv.appendChild(span);

    span = document.createElement("span");
    span.className = "progress";

    var span2 = document.createElement("span");
    span2.id = "progressBar";
    span2.className = "bar";
    span2.appendChild(document.createTextNode("0%"));
    span.appendChild(span2);

    statusdiv.appendChild(span);
    statusdiv.appendChild(document.createElement("br"));
    statusdiv.appendChild(document.createElement("br"));
    sesame('openmax',statusdiv);

    add_to_dev_info("Posted to QUERY",queryObj);
    fetch(baseAPI + "api/rtx/v1/query", {
	method: 'post',
	body: JSON.stringify(queryObj),
	headers: { 'Content-type': 'application/json' }
    }).then(function(response) {
	var reader = response.body.getReader();
	var partialMsg = '';
	var enqueue = false;
	var numCurrMsgs = 0;
	var totalSteps = 0;
	var finishedSteps = 0;
	var decoder = new TextDecoder();
	var respjson = '';

	function scan() {
	    return reader.read().then(function(result) {
		partialMsg += decoder.decode(result.value || new Uint8Array, {
		    stream: !result.done
		});

		var completeMsgs = partialMsg.split("\n");
		//console.log("================ completeMsgs::");
		//console.log(completeMsgs);

		if (!result.done) {
		    // Last msg is likely incomplete; hold it for next time
		    partialMsg = completeMsgs[completeMsgs.length - 1];
		    // Remove it from our complete msgs
		    completeMsgs = completeMsgs.slice(0, -1);
		}

		for (var msg of completeMsgs) {
		    msg = msg.trim();
		    if (msg == null) continue;

		    //console.log("================ msg::");
		    //console.log(msg);

		    if (enqueue) {
			respjson += msg;
		    }
		    else {
			var jsonMsg = JSON.parse(msg);
			if (jsonMsg.code_description) {
			    enqueue = true;
			    respjson += msg;
			}
			else if (jsonMsg.message) {
			    if (jsonMsg.message.match(/^Parsing action: [^\#]\S+/)) {
				totalSteps++;
			    }
			    else if (totalSteps>0) {
				document.getElementById("totalSteps").innerHTML = totalSteps;
				if (numCurrMsgs < 99)
				    numCurrMsgs++;
				if (finishedSteps == totalSteps)
				    numCurrMsgs = 1;

                                document.getElementById("progressBar").style.width = (800*(finishedSteps+0.5*Math.log10(numCurrMsgs))/totalSteps)+"px";
				document.getElementById("progressBar").innerHTML = Math.round(99*(finishedSteps+0.5*Math.log10(numCurrMsgs))/totalSteps)+"%\u00A0\u00A0";

				if (jsonMsg.message.match(/^Processing action/)) {
				    finishedSteps++;
				    document.getElementById("finishedSteps").innerHTML = finishedSteps;
				    numCurrMsgs = 0;
				}
			    }

			    cmddiv.appendChild(document.createTextNode(jsonMsg.prefix+'\u00A0'+jsonMsg.message));
			    cmddiv.appendChild(document.createElement("br"));
			    cmddiv.scrollTop = cmddiv.scrollHeight;
			}
			else {
			    console.log("bad msg:"+jsonMsg);
			}
		    }
		}

		if (result.done) {
		    //console.log(respjson);
		    return respjson;
		}

		return scan();
	    })
	}
	return scan();
    })
        .then(response => {
	    var data = JSON.parse(response);

	    var dev = document.getElementById("devdiv");
            dev.appendChild(document.createElement("br"));
	    dev.appendChild(document.createTextNode('='.repeat(80)+" RESPONSE MESSAGE::"));
	    var pre = document.createElement("pre");
	    pre.id = "responseJSON";
	    pre.appendChild(document.createTextNode(JSON.stringify(data,null,2)));
	    dev.appendChild(pre);

	    document.getElementById("progressBar").style.width = "800px";
	    if (data.message_code == "OK")
		document.getElementById("progressBar").innerHTML = "Finished\u00A0\u00A0";
	    else {
		document.getElementById("progressBar").classList.add("barerror");
		document.getElementById("progressBar").innerHTML = "Error\u00A0\u00A0";
		document.getElementById("finishedSteps").classList.add("menunum","numnew","msgERROR");
		there_was_an_error();
	    }
	    statusdiv.appendChild(document.createTextNode(data["code_description"]));  // italics?
	    statusdiv.appendChild(document.createElement("br"));
	    sesame('openmax',statusdiv);

	    if (data["message_code"] == "QueryGraphZeroNodes") {
		clear_qg();
	    }
	    else if (data["message_code"] == "OK") {
		input_qg = { "edges": [], "nodes": [] };
		render_message(data,qtype == "DSL");
	    }
	    else if (data["log"]) {
		process_log(data["log"]);
	    }
	    else {
		statusdiv.innerHTML += "<br><span class='error'>An error was encountered while parsing the response from the server (no log; code:"+data.message_code+")</span>";
		document.getElementById("devdiv").innerHTML += "------------------------------------ error with capturing QUERY:<br>"+data;
		sesame('openmax',statusdiv);
	    }

	})
        .catch(function(err) {
	    statusdiv.innerHTML += "<br><span class='error'>An error was encountered while contacting the server ("+err+")</span>";
	    document.getElementById("devdiv").innerHTML += "------------------------------------ error with parsing QUERY:<br>"+err;
	    sesame('openmax',statusdiv);
	    if (err.log) {
		process_log(err.log);
	    }
	    console.log(err.message);
            there_was_an_error();
	});
}


function sendQuestion(e) {
    reset_vars();
    if (cyobj[999]) {cyobj[999].elements().remove();}
    input_qg = { "edges": [], "nodes": [] };

    var bypass_cache = "true";
    if (document.getElementById("useCache").checked) {
	bypass_cache = "false";
    }

    // collect the form data while iterating over the inputs
    var q = document.getElementById("questionForm").elements["questionText"].value;
    var question = q.replace("[A]", get_list_as_string("A"));
    question = question.replace("[B]", get_list_as_string("B"));
    question = question.replace("[]", get_list_as_string("A"));
    question = question.replace(/\$\w+_list/, get_list_as_string("A"));  // e.g. $protein_list
    var data = { 'text': question, 'language': 'English', 'bypass_cache' : bypass_cache };
    document.getElementById("statusdiv").innerHTML = "Interpreting your question...";
    document.getElementById("devdiv").innerHTML = " (bypassing cache : " + bypass_cache + ")";

    sesame('openmax',statusdiv);
    document.getElementById('qg_form').style.visibility = 'hidden';
    document.getElementById('qg_form').style.maxHeight = null;

    // construct an HTTP request
    var xhr = new XMLHttpRequest();
    xhr.open("post", baseAPI + "api/rtx/v1/translate", true);
    xhr.setRequestHeader('Content-Type', 'application/json; charset=UTF-8');

    // send the collected data as JSON
    xhr.send(JSON.stringify(data));

    xhr.onloadend = function() {
	if ( xhr.status == 200 ) {
	    var jsonObj = JSON.parse(xhr.responseText);
	    add_to_dev_info("Posted to TRANSLATE",jsonObj);

	    if ( jsonObj.query_type_id && jsonObj.terms ) {
		document.getElementById("statusdiv").innerHTML = "Your question has been interpreted and is restated as follows:<br>&nbsp;&nbsp;&nbsp;<b>"+jsonObj["restated_question"]+"?</b><br>Please ensure that this is an accurate restatement of the intended question.<br>Looking for answer...";

		sesame('openmax',statusdiv);
		var xhr2 = new XMLHttpRequest();
		xhr2.open("post",  baseAPI + "api/rtx/v1/query", true);
		xhr2.setRequestHeader('Content-Type', 'application/json; charset=UTF-8');

                var queryObj = { "message" : jsonObj };
                queryObj.bypass_cache = bypass_cache;
                queryObj.max_results = 100;

		add_to_dev_info("Posted to QUERY",queryObj);
		xhr2.send(JSON.stringify(queryObj));
		xhr2.onloadend = function() {
		    if ( xhr2.status == 200 ) {
			var jsonObj2 = JSON.parse(xhr2.responseText);
			document.getElementById("devdiv").innerHTML += "<br>================================================================= QUERY::<pre id='responseJSON'>\n" + JSON.stringify(jsonObj2,null,2) + "</pre>";

			document.getElementById("statusdiv").innerHTML = "Your question has been interpreted and is restated as follows:<br>&nbsp;&nbsp;&nbsp;<b>"+jsonObj2["restated_question"]+"?</b><br>Please ensure that this is an accurate restatement of the intended question.<br><br><i>"+jsonObj2["code_description"]+"</i><br>";
			sesame('openmax',statusdiv);

			render_message(jsonObj2,true);
		    }
		    else if ( jsonObj.message ) { // STILL APPLIES TO 0.9??  TODO
			document.getElementById("statusdiv").innerHTML += "<br><br>An error was encountered:<br><span class='error'>"+jsonObj.message+"</span>";
			sesame('openmax',statusdiv);
		    }
		    else {
			document.getElementById("statusdiv").innerHTML += "<br><span class='error'>An error was encountered while contacting the server ("+xhr2.status+")</span>";
			document.getElementById("devdiv").innerHTML += "------------------------------------ error with QUERY:<br>"+xhr2.responseText;
			sesame('openmax',statusdiv);
		    }

		};
	    }
	    else {
		if ( jsonObj.message ) {
		    document.getElementById("statusdiv").innerHTML = jsonObj.message;
		}
		else if ( jsonObj.error_message ) {
		    document.getElementById("statusdiv").innerHTML = jsonObj.error_message;
		}
		else {
		    document.getElementById("statusdiv").innerHTML = "ERROR: Unknown error. No message returned.";
		}
		sesame('openmax',statusdiv);
	    }

	}
	else { // responseText
	    document.getElementById("statusdiv").innerHTML += "<br><br>An error was encountered:<br><span class='error'>"+xhr.statusText+" ("+xhr.status+")</span>";
	    sesame('openmax',statusdiv);
	}
    };

}


function retrieve_message() {
    var statusdiv = document.getElementById("statusdiv");
    statusdiv.appendChild(document.createTextNode("Retrieving ARAX message id = " + message_id));
    statusdiv.appendChild(document.createElement("hr"));
    sesame('openmax',statusdiv);

    var xhr = new XMLHttpRequest();
    xhr.open("get",  baseAPI + "api/rtx/v1/message/" + message_id, true);
    xhr.setRequestHeader('Content-Type', 'application/json; charset=UTF-8');
    xhr.send(null);
    xhr.onloadend = function() {
	if ( xhr.status == 200 ) {
	    var jsonObj2 = JSON.parse(xhr.responseText);
	    document.getElementById("devdiv").innerHTML += "<br>================================================================= RESPONSE REQUEST::<pre id='responseJSON'>\n" + JSON.stringify(jsonObj2,null,2) + "</pre>";

	    if (jsonObj2["restated_question"].length > 2) {
		statusdiv.innerHTML += "Your question has been interpreted and is restated as follows:<br>&nbsp;&nbsp;&nbsp;<B>"+jsonObj2["restated_question"]+"?</b><br>Please ensure that this is an accurate restatement of the intended question.<br>";
		document.getElementById("questionForm").elements["questionText"].value = jsonObj2["restated_question"];
	    }
	    else {
		document.getElementById("questionForm").elements["questionText"].value = "";
	    }
	    statusdiv.innerHTML += "<br><i>"+jsonObj2["code_description"]+"</i><br>";
	    sesame('openmax',statusdiv);

	    render_message(jsonObj2,true);
	}
	else if ( xhr.status == 404 ) {
	    statusdiv.innerHTML += "<br>Message with id=<span class='error'>"+message_id+"</span> was not found.";
	    sesame('openmax',statusdiv);
	    there_was_an_error();
	}
	else {
	    statusdiv.innerHTML += "<br><span class='error'>An error was encountered while contacting the server ("+xhr.status+")</span>";
	    document.getElementById("devdiv").innerHTML += "------------------------------------ error with RESPONSE:<br>"+xhr.responseText;
	    sesame('openmax',statusdiv);
            there_was_an_error();
	}
    };
}


function render_message(respObj,dispjson) {
    var statusdiv = document.getElementById("statusdiv");
    statusdiv.appendChild(document.createTextNode("Rendering message..."));
    sesame('openmax',statusdiv);

    if (respObj.id) {
	message_id = respObj.id.substr(respObj.id.lastIndexOf('/') + 1);

	if (respObj.restated_question.length > 2)
	    add_to_session(message_id,respObj.restated_question+"?");
	else
	    add_to_session(message_id,"message="+message_id);

	document.title = "ARAX-UI ["+message_id+"]: "+respObj.restated_question+"?";
	history.pushState({ id: 'ARAX_UI' }, 'ARAX | message='+message_id, "//"+ window.location.hostname + window.location.pathname + '?m='+message_id);
    }
    else {
        document.title = "ARAX-UI [no message_id]: "+respObj.restated_question+"?";
    }

    if ( respObj["table_column_names"] ) {
	add_to_summary(respObj["table_column_names"],0);
    }
    if ( respObj["results"] ) {
	if (!respObj["knowledge_graph"] ) {
            document.getElementById("result_container").innerHTML  += "<h2 class='error'>Knowledge Graph missing in response; cannot process results.</h2>";
	    document.getElementById("summary_container").innerHTML += "<h2 class='error'>Knowledge Graph missing in response; cannot process results</h2>";
	}
	else {
            document.getElementById("result_container").innerHTML += "<h2>" + respObj["n_results"] + " results</h2>";
            document.getElementById("menunumresults").innerHTML = respObj["n_results"];
            document.getElementById("menunumresults").classList.add("numnew");
	    document.getElementById("menunumresults").classList.remove("numold");

	    process_graph(respObj["knowledge_graph"],0);
	    process_results(respObj["results"],respObj["knowledge_graph"]);
	}
    }
    else {
        document.getElementById("result_container").innerHTML  += "<h2>No results...</h2>";
        document.getElementById("summary_container").innerHTML += "<h2>No results...</h2>";
    }


    if (respObj["query_graph"]) {
	if (dispjson) {
	    for (var gnode of respObj["query_graph"].nodes)
		for (var att in gnode)
		    if (gnode.hasOwnProperty(att))
			if (gnode[att] == null)
			    delete gnode[att];
            for (var gedge of respObj["query_graph"].edges)
		for (var att in gedge)
		    if (gedge.hasOwnProperty(att))
			if (gedge[att] == null)
			    delete gedge[att];
	    document.getElementById("jsonText").value = JSON.stringify(respObj["query_graph"],null,2);
	}
	process_graph(respObj["query_graph"],999);
    }
    else
	cytodata[999] = 'dummy'; // this enables query graph editing


    if (respObj["table_column_names"]) {
	var div = document.createElement("div");
	div.className = 'statushead';
	div.appendChild(document.createTextNode("Summary"));
        document.getElementById("summary_container").appendChild(div);

	div = document.createElement("div");
	div.className = 'status';
	div.id = 'summarydiv';
	div.appendChild(document.createElement("br"));

	var button = document.createElement("input");
	button.className = 'questionBox button';
	button.type = 'button';
	button.name = 'action';
	button.title = 'Get tab-separated values of this table to paste into Excel etc';
	button.value = 'Copy Summary Table to clipboard (TSV)';
	button.setAttribute('onclick', 'copyTSVToClipboard(this);');
        div.appendChild(button);

        div.appendChild(document.createElement("br"));
	div.appendChild(document.createElement("br"));

	var table = document.createElement("table");
	table.className = 'sumtab';
	table.innerHTML = summary_table_html;
        div.appendChild(table);

	div.appendChild(document.createElement("br"));

	document.getElementById("summary_container").appendChild(div);
    }
    else
        document.getElementById("summary_container").innerHTML += "<h2>Summary not available for this query</h2>";


    if (respObj["query_options"])
	process_q_options(respObj["query_options"]);


    if (respObj["log"])
	process_log(respObj["log"]);
    else
        document.getElementById("logdiv").innerHTML = "<h2 style='margin-left:20px;'>No log messages in this response</h2>";

    add_cyto();
    statusdiv.appendChild(document.createTextNode("done."));
    sesame('openmax',statusdiv);
}


function process_q_options(q_opts) {
    if (q_opts.processing_actions) {
	clearDSL();
	for (var act of q_opts.processing_actions) {
	    document.getElementById("dslText").value += act + "\n";
	}
    }
}


function there_was_an_error() {
    document.getElementById("summary_container").innerHTML += "<h2 class='error'>Error : No results</h2>";
    document.getElementById("result_container").innerHTML  += "<h2 class='error'>Error : No results</h2>";
    document.getElementById("menunumresults").innerHTML = "E";
    document.getElementById("menunumresults").classList.add("numnew","msgERROR");
    document.getElementById("menunumresults").classList.remove("numold");
}

function process_log(logarr) {
    var status = {};
    for (var s of ["ERROR","WARNING","INFO","DEBUG"]) {
	status[s] = 0;
    }
    for (var msg of logarr) {
	status[msg.level_str]++;

	var span = document.createElement("span");
	span.className = "hoverable msg " + msg.level_str;

        if (msg.level_str == "DEBUG") { span.style.display = 'none'; }

	var span2 = document.createElement("span");
	span2.className = "explevel msg" + msg.level_str;
	span2.appendChild(document.createTextNode('\u00A0'));
	span2.appendChild(document.createTextNode('\u00A0'));
        span.appendChild(span2);

	span.appendChild(document.createTextNode('\u00A0'));

	span.appendChild(document.createTextNode(msg.prefix));
//	span.appendChild(document.createElement("br"));

	span.appendChild(document.createTextNode('\u00A0'));
	span.appendChild(document.createTextNode('\u00A0'));
	span.appendChild(document.createTextNode('\u00A0'));
	span.appendChild(document.createTextNode(msg.message));

	document.getElementById("logdiv").appendChild(span);
    }
    document.getElementById("menunummessages").innerHTML = logarr.length;
    if (status.ERROR > 0) document.getElementById("menunummessages").classList.add('numnew','msgERROR');
    else if (status.WARNING > 0) document.getElementById("menunummessages").classList.add('numnew','msgWARNING');
    for (var s of ["ERROR","WARNING","INFO","DEBUG"]) {
	document.getElementById("count_"+s).innerHTML += ": "+status[s];
    }
}


function add_status_divs() {
    // summary
    document.getElementById("status_container").innerHTML = '';

    var div = document.createElement("div");
    div.className = 'statushead';
    div.appendChild(document.createTextNode("Status"));
    document.getElementById("status_container").appendChild(div);

    div = document.createElement("div");
    div.className = 'status';
    div.id = 'statusdiv';
    document.getElementById("status_container").appendChild(div);

    // results
    document.getElementById("dev_result_json_container").innerHTML = '';

    div = document.createElement("div");
    div.className = 'statushead';
    div.appendChild(document.createTextNode("Dev Info"));
    var span = document.createElement("span");
    span.style.fontStyle = "italic";
    span.style.fontWeight = 'normal';
    span.style.float = "right";
    span.appendChild(document.createTextNode("( json responses )"));
    div.appendChild(span);
    document.getElementById("dev_result_json_container").appendChild(div);

    div = document.createElement("div");
    div.className = 'status';
    div.id = 'devdiv';
    document.getElementById("dev_result_json_container").appendChild(div);

    // messages
    document.getElementById("messages_container").innerHTML = '';

    div = document.createElement("div");
    div.className = 'statushead';
    div.appendChild(document.createTextNode("Filter Messages:"));

    for (var status of ["Error","Warning","Info","Debug"]) {
	span = document.createElement("span");
	span.id =  'count_'+status.toUpperCase();
	span.style.marginLeft = "20px";
	span.style.cursor = "pointer";
	span.className = 'qprob msg'+status.toUpperCase();
	if (status == "Debug") span.classList.add('hide');
	span.setAttribute('onclick', 'filtermsgs(this,\"'+status.toUpperCase()+'\");');
	span.appendChild(document.createTextNode(status));
	div.appendChild(span);
    }

    document.getElementById("messages_container").appendChild(div);

    div = document.createElement("div");
    div.className = 'status';
    div.id = 'logdiv';
    document.getElementById("messages_container").appendChild(div);
}

function filtermsgs(span, type) {
    var disp = 'none';
    if (span.classList.contains('hide')) {
	disp = '';
	span.classList.remove('hide');
    }
    else {
	span.classList.add('hide');
    }

    for (var msg of document.getElementById("logdiv").children) {
	if (msg.classList.contains(type)) {
	    msg.style.display = disp;
	}
    }
}


function add_to_summary(rowdata, num) {
    var cell = 'td';
    if (num == 0) {
	cell = 'th';
	summary_table_html += "<tr><th>&nbsp;</th>";
    }
    else {
	summary_table_html += "<tr class='hoverable'><td>"+num+".</td>";
    }

    for (var i in rowdata) {
	var listlink = '';
	if (cell == 'th') {
	    columnlist[i] = [];
	    if (rowdata[i] != 'confidence') {
		listlink += "&nbsp;<a href='javascript:add_items_to_list(\"A\",\"" +i+ "\");' title='Add column items to list A'>&nbsp;[+A]&nbsp;</a>";
		listlink += "&nbsp;<a href='javascript:add_items_to_list(\"B\",\"" +i+ "\");' title='Add column items to list B'>&nbsp;[+B]&nbsp;</a>";
	    }
	}
	else {
	    columnlist[i][rowdata[i]] = 1;
	}
	summary_table_html += '<'+cell+'>' + rowdata[i] + listlink + '</'+cell+'>';
    }
    summary_table_html += '</tr>';

    summary_tsv.push(rowdata.join("\t"));
}


function process_graph(gne,gid) {
    cytodata[gid] = [];
    for (var gnode of gne.nodes) {
	gnode.parentdivnum = gid; // helps link node to div when displaying node info on click
	if (gnode.node_id) { // deal with QueryGraphNode (QNode)
	    gnode.id = gnode.node_id;
	}
	if (gnode.curie) {
	    if (gnode.name) {
		gnode.name += " ("+gnode.curie+")";
	    }
	    else {
		gnode.name = gnode.curie;
	    }
	}
	if (!gnode.name) {
	    if (gnode.type)
		gnode.name = gnode.type + "s?";
	    else
		gnode.name = "(Any)";
	}

        var tmpdata = { "data" : gnode };
        cytodata[gid].push(tmpdata);
    }

    for (var gedge of gne.edges) {
	gedge.parentdivnum = gid;
        gedge.source = gedge.source_id;
        gedge.target = gedge.target_id;

        var tmpdata = { "data" : gedge }; // already contains id(?)
        cytodata[gid].push(tmpdata);
    }


    if (gid == 999) {
	for (var gnode of gne.nodes) {
	    qgids.push(gnode.id);

	    var tmpdata = { "id"     : gnode.id,
			    "is_set" : gnode.is_set,
			    "name"   : gnode.name,
			    "desc"   : gnode.description,
			    "curie"  : gnode.curie,
			    "type"   : gnode.type
			  };

	    input_qg.nodes.push(tmpdata);
	}

	for (var gedge of gne.edges) {
	    qgids.push(gedge.id);

	    var tmpdata = { "id"       : gedge.id,
			    "negated"  : null,
			    "relation" : null,
			    "source_id": gedge.source_id,
			    "target_id": gedge.target_id,
			    "type"     : gedge.type
			  };
	    input_qg.edges.push(tmpdata);
	}
    }

}


function process_results(reslist,kg) {
    for (var i = 0; i < reslist.length; i++) {
	var num = Number(i) + 1;

        if ( reslist[i].row_data ) {
            add_to_summary(reslist[i].row_data, num);
	}

	var ess = '';
	if (reslist[i].essence) {
	    ess = reslist[i].essence;
	}
	var cnf = 0;
	if (Number(reslist[i].confidence)) {
	    cnf = Number(reslist[i].confidence).toFixed(2);
	}
	var pcl = (cnf>=0.9) ? "p9" : (cnf>=0.7) ? "p7" : (cnf>=0.5) ? "p5" : (cnf>=0.3) ? "p3" : "p1";

	var rsrc = '';
	if (reslist[i].reasoner_id) {
	    rsrc = reslist[i].reasoner_id;
	}
	var rscl = (rsrc=="ARAX") ? "srtx" : (rsrc=="Indigo") ? "sind" : (rsrc=="Robokop") ? "srob" : "p0";

	
        document.getElementById("result_container").innerHTML += "<div onclick='sesame(this,a"+num+"_div);' id='h"+num+"_div' title='Click to expand / collapse result "+num+"' class='accordion'>Result "+num+" :: <b>"+ess+"</b><span class='r100'><span title='confidence="+cnf+"' class='"+pcl+" qprob'>"+cnf+"</span><span title='source="+rsrc+"' class='"+rscl+" qprob'>"+rsrc+"</span></span></div>";

	document.getElementById("result_container").innerHTML += "<div id='a"+num+"_div' class='panel'><table class='t100'><tr><td class='textanswer'>"+reslist[i].description+"</td><td class='cytograph_controls'><a title='reset zoom and center' onclick='cyobj["+num+"].reset();'>&#8635;</a><br><a title='breadthfirst layout' onclick='cylayout("+num+",\"breadthfirst\");'>B</a><br><a title='force-directed layout' onclick='cylayout("+num+",\"cose\");'>F</a><br><a title='circle layout' onclick='cylayout("+num+",\"circle\");'>C</a><br><a title='random layout' onclick='cylayout("+num+",\"random\");'>R</a>	</td><td class='cytograph'><div style='height: 100%; width: 100%' id='cy"+num+"'></div></td></tr><tr><td>&nbsp;</td><td></td><td><div id='d"+num+"_div'><i>Click on a node or edge to get details</i></div></td></tr></table></div>";

        cytodata[num] = [];

	//console.log("=================== CYTO i:"+i+"  #nb:"+reslist[i].node_bindings.length);

        for (var nb of reslist[i].node_bindings) {
	    //console.log("=================== i:"+i+"  item:"+nb);
	    var kmne = Object.create(kg.nodes.find(item => item.id == nb.kg_id));
            kmne.parentdivnum = num;
            //console.log("=================== kmne:"+kmne.id);
	    var tmpdata = { "data" : kmne };
	    cytodata[num].push(tmpdata);
	}

	for (var eb of reslist[i].edge_bindings) {
	    if (Array.isArray(eb.kg_id)) {
		for (var kgid of eb.kg_id) {
                    var kmne = Object.create(kg.edges.find(item => item.id == kgid));
		    kmne.parentdivnum = num;
		    //console.log("=================== kmne:"+kmne.id);

		    var tmpdata = { "data" : kmne };
		    cytodata[num].push(tmpdata);
		}
	    }
	    else {
		var kmne = Object.create(kg.edges.find(item => item.id == eb.kg_id));
		kmne.parentdivnum = num;
		//console.log("=================== kmne:"+kmne.id);

		var tmpdata = { "data" : kmne };
		cytodata[num].push(tmpdata);
	    }
	}
    }
}


function add_cyto() {
    for (var i in cytodata) {
	if (cytodata[i] == null) continue;

	var num = Number(i);// + 1;

	//console.log("---------------cyto i="+i);
	cyobj[i] = cytoscape({
	    container: document.getElementById('cy'+num),
	    style: cytoscape.stylesheet()
		.selector('node')
		.css({
		    'background-color': function(ele) { return mapNodeColor(ele); } ,
		    'shape': function(ele) { return mapNodeShape(ele); } ,
		    'border-color' : '#000',
		    'border-width' : '2',
		    'width': '20',
		    'height': '20',
		    'content': 'data(name)'
		})
		.selector('edge')
		.css({
		    'curve-style' : 'bezier',
		    'line-color': function(ele) { return mapEdgeColor(ele); } ,
		    'target-arrow-color': function(ele) { return mapEdgeColor(ele); } ,
		    'width': function(ele) { if (ele.data().weight) { return ele.data().weight; } return 2; },
		    'target-arrow-shape': 'triangle',
		    'opacity': 0.8,
		    'content': function(ele) { if ((ele.data().parentdivnum > 900) && ele.data().type) { return ele.data().type; } return '';}
		})
		.selector(':selected')
		.css({
		    'background-color': '#ff0',
		    'border-color': '#f80',
		    'line-color': '#f80',
		    'target-arrow-color': '#f80',
		    'source-arrow-color': '#f80',
		    'opacity': 1
		})
		.selector('.faded')
		.css({
		    'opacity': 0.25,
		    'text-opacity': 0
		}),

	    elements: cytodata[i],

	    wheelSensitivity: 0.2,

	    layout: {
		name: 'breadthfirst',
		padding: 10
	    },

	    ready: function() {
		// ready 1
	    }
	});

	if (i > 900) {
	    cyobj[i].on('tap','node', function() {
		document.getElementById('qg_edge_n'+UIstate.nodedd).value = this.data('id');
		UIstate.nodedd = 3 - UIstate.nodedd;
		get_possible_edges();
	    });

	    return;
	}

	cyobj[i].on('tap','node', function() {
	    var div = document.getElementById('d'+this.data('parentdivnum')+'_div');
	    div.innerHTML = "";

            var fields = [ "name","id","uri","type" ];
	    if (this.data('description') !== 'UNKNOWN' && this.data('description') !== 'None')
		fields.push("description");

	    for (var field of fields) {
		if (this.data(field)) {
		    var span = document.createElement("span");
		    span.className = "fieldname";
		    span.appendChild(document.createTextNode(field+": "));
		    div.appendChild(span);
		    if (field == "uri") {
			var link = document.createElement("a");
			link.href = this.data(field);
			link.target = "nodeuri";
			link.appendChild(document.createTextNode(this.data(field)));
			div.appendChild(link);
		    }
		    else {
			div.appendChild(document.createTextNode(this.data(field)));
		    }
		    div.appendChild(document.createElement("br"));
		}
	    }

	    show_attributes(div, this.data('node_attributes'));

	    sesame('openmax',document.getElementById('a'+this.data('parentdivnum')+'_div'));
	});

	cyobj[i].on('tap','edge', function() {
            var div = document.getElementById('d'+this.data('parentdivnum')+'_div');
	    div.innerHTML = "";

            div.appendChild(document.createTextNode(this.data('source')+" "));
            var span = document.createElement("b");
	    span.appendChild(document.createTextNode(this.data('type')));
            div.appendChild(span);
	    div.appendChild(document.createTextNode(" "+this.data('target')));
            div.appendChild(document.createElement("br"));

	    var tmpArr = [];
	    if (!(Array.isArray(this.data('provided_by'))))
		tmpArr.push(this.data('provided_by'));
	    else
		tmpArr = this.data('provided_by');

            for (var prov of tmpArr) {
		if (prov == null) continue;

		span = document.createElement("span");
		span.className = "fieldname";
		span.appendChild(document.createTextNode("Provenance: "));
		div.appendChild(span);

		if (prov.startsWith("http")) {
		    var provlink = document.createElement("a");
		    provlink.href = prov;
		    provlink.target = "prov";
		    provlink.appendChild(document.createTextNode(prov));
		    div.appendChild(provlink);
		}
		else {
                    div.appendChild(document.createTextNode(prov));
		}
                div.appendChild(document.createElement("br"));
	    }


	    var fields = [ "confidence","weight","evidence_type","qualifiers","negated",
			   "relation","is_defined_by","defined_datetime","id","qedge_id" ];
	    for (var field of fields) {
		if (this.data(field) == null) continue;

		span = document.createElement("span");
		span.className = "fieldname";
		span.appendChild(document.createTextNode(field+": "));
		div.appendChild(span);
		if (field == "confidence" || field == "weight") {
		    div.appendChild(document.createTextNode(Number(this.data(field)).toPrecision(3)));
		}
                else if (this.data(field).toString().startsWith("http")) {
		    var link = document.createElement("a");
		    link.href = this.data(field);
		    link.target = "nodeuri";
		    link.appendChild(document.createTextNode(this.data(field)));
		    div.appendChild(link);
		}
		else {
		    div.appendChild(document.createTextNode(this.data(field)));
		}
		div.appendChild(document.createElement("br"));
	    }

            tmpArr = [];
	    if (!(Array.isArray(this.data('publications'))))
		tmpArr.push(this.data('publications'));
	    else
		tmpArr = this.data('publications');

	    for (var pub of tmpArr) {
		if (pub == null) continue;

		span = document.createElement("span");
		span.className = "fieldname";
		span.appendChild(document.createTextNode("Publication: "));
		div.appendChild(span);

		if (pub.startsWith("PMID:")) {
		    var publink = document.createElement("a");
		    publink.href = "https://www.ncbi.nlm.nih.gov/pubmed/" + pub.split(":")[1];
		    publink.target = "pubmed";
		    publink.appendChild(document.createTextNode(pub));
		    div.appendChild(publink);
		}
		else {
		    div.appendChild(document.createTextNode(pub));
		}
		div.appendChild(document.createElement("br"));
	    }

	    show_attributes(div, this.data('edge_attributes'));

	    sesame('openmax',document.getElementById('a'+this.data('parentdivnum')+'_div'));
	});

    }

}

function show_attributes(html_div, atts) {
    if (atts == null)  { return; }

    var linebreak = "<hr>";

    for (var att of atts) {
	var snippet = linebreak;

	if (att.name != null) {
	    snippet += "<b>" + att.name + "</b>";
	    if (att.type != null)
		snippet += " (" + att.type + ")";
	    snippet += ": ";
	}
	if (att.url != null)
	    snippet += "<a target='araxext' href='" + att.url + "'>";


	if (att.value != null) {
	    if (att.name == "probability_drug_treats" ||
		att.name == "observed_expected_ratio" ||
		att.name == "paired_concept_frequency"||
		att.name == "paired_concept_freq"     ||
		att.name == "jaccard_index"           ||
		att.name == "probability"             ||
		att.name == "chi_square"              ||
		att.name == "ngd") {
		snippet += Number(att.value).toPrecision(3);
	    }
            else if (Array.isArray(att.value))
		for (var val of att.value) snippet += "<br>"+val;
	    else
		snippet += att.value;

	}
	else if (att.url != null)
	    snippet += att.url;
	else
	    snippet += " n/a ";


	if (att.url != null)
	    snippet += "</a>";

	html_div.innerHTML+= snippet;
	linebreak = "<br>";
    }

}


function cylayout(index,layname) {
    var layout = cyobj[index].layout({
	idealEdgeLength: 100,
        nodeOverlap: 20,
	refresh: 20,
        fit: true,
        padding: 30,
        componentSpacing: 100,
        nodeRepulsion: 10000,
        edgeElasticity: 100,
        nestingFactor: 5,
	name: layname,
	animationDuration: 500,
	animate: 'end'
    });

    layout.run();
}

function mapNodeShape (ele) {
    var ntype = ele.data().type;
    if (ntype == "microRNA")           { return "hexagon";}
    if (ntype == "metabolite")         { return "heptagon";}
    if (ntype == "protein")            { return "octagon";}
    if (ntype == "pathway")            { return "vee";}
    if (ntype == "disease")            { return "triangle";}
    if (ntype == "molecular_function") { return "rectangle";}
    if (ntype == "cellular_component") { return "ellipse";}
    if (ntype == "biological_process") { return "tag";}
    if (ntype == "chemical_substance") { return "diamond";}
    if (ntype == "anatomical_entity")  { return "rhomboid";}
    if (ntype == "phenotypic_feature") { return "star";}
    return "rectangle";
}

function mapNodeColor (ele) {
    var ntype = ele.data().type;
    if (ntype == "microRNA")           { return "orange";}
    if (ntype == "metabolite")         { return "aqua";}
    if (ntype == "protein")            { return "black";}
    if (ntype == "pathway")            { return "gray";}
    if (ntype == "disease")            { return "red";}
    if (ntype == "molecular_function") { return "blue";}
    if (ntype == "cellular_component") { return "purple";}
    if (ntype == "biological_process") { return "green";}
    if (ntype == "chemical_substance") { return "yellowgreen";}
    if (ntype == "anatomical_entity")  { return "violet";}
    if (ntype == "phenotypic_feature") { return "indigo";}
    return "#04c";
}

function mapEdgeColor (ele) {
    var etype = ele.data().type;
    if (etype == "contraindicated_for")       { return "red";}
    if (etype == "indicated_for")             { return "green";}
    if (etype == "physically_interacts_with") { return "green";}
    return "#aaf";
}

function edit_qg() {
    cytodata[999] = [];
    if (cyobj[999]) {cyobj[999].elements().remove();}

    for (var gnode of input_qg.nodes) {
	var name = "";

	if (gnode.name)       { name = gnode.name;}
	else if (gnode.curie) { name = gnode.curie;}
	else if (gnode.type)  { name = gnode.type + "s?";}
	else                  { name = "(Any)";}

        cyobj[999].add( {
	    "data" : {
		"id"   : gnode.id,
		"name" : name,
		"type" : gnode.type,
		"parentdivnum" : 999 },
//	    "position" : {x:100*(qgid-nn), y:50+nn*50}
	} );
    }

    for (var gedge of input_qg.edges) {
	cyobj[999].add( {
	    "data" : {
		"id"     : gedge.id,
		"source" : gedge.source_id,
		"target" : gedge.target_id,
		"type"   : gedge.type,
		"parentdivnum" : 999 }
	} );
    }

    cylayout(999,"breadthfirst");
    document.getElementById('qg_form').style.visibility = 'visible';
    document.getElementById('qg_form').style.maxHeight = "100%";
    update_kg_edge_input();
    display_query_graph_items();

    document.getElementById("devdiv").innerHTML +=  "Copied query_graph to edit window<br>";
}


function display_query_graph_items() {
    var table = document.createElement("table");
    table.className = 'sumtab';

    var tr = document.createElement("tr");
    for (var head of ["Id","Name","Item","Type","Action"] ) {
	var th = document.createElement("th")
	th.appendChild(document.createTextNode(head));
	tr.appendChild(th);
    }
    table.appendChild(tr);

    var nitems = 0;

    input_qg.nodes.forEach(function(result, index) {
	nitems++;

	tr = document.createElement("tr");
	tr.className = 'hoverable';

	var td = document.createElement("td");
        td.appendChild(document.createTextNode(result.id));
        tr.appendChild(td);

        td = document.createElement("td");
        td.appendChild(document.createTextNode(result.name == null ? "-" : result.name));
        tr.appendChild(td);

	td = document.createElement("td");
        td.appendChild(document.createTextNode(result.is_set ? "(multiple items)" : result.curie == null ? "(any node)" : result.curie));
        tr.appendChild(td);

	td = document.createElement("td");
        td.appendChild(document.createTextNode(result.is_set ? "(set of nodes)" : result.type == null ? "(any)" : result.type));
        tr.appendChild(td);

        td = document.createElement("td");
	var link = document.createElement("a");
	link.href = 'javascript:remove_node_from_query_graph(\"'+result.id+'\")';
	link.appendChild(document.createTextNode(" Remove "));
	td.appendChild(link);
        tr.appendChild(td);

	table.appendChild(tr);
    });

    input_qg.edges.forEach(function(result, index) {
        tr = document.createElement("tr");
	tr.className = 'hoverable';

	var td = document.createElement("td");
        td.appendChild(document.createTextNode(result.id));
	tr.appendChild(td);

	td = document.createElement("td");
        td.appendChild(document.createTextNode("-"));
        tr.appendChild(td);

        td = document.createElement("td");
	td.appendChild(document.createTextNode(result.source_id+"--"+result.target_id));
	tr.appendChild(td);

        td = document.createElement("td");
	td.appendChild(document.createTextNode(result.type == null ? "(any)" : result.type));
	tr.appendChild(td);

        td = document.createElement("td");
	var link = document.createElement("a");
	link.href = 'javascript:remove_edge_from_query_graph(\"'+result.id+'\")';
	link.appendChild(document.createTextNode(" Remove "));
	td.appendChild(link);
	tr.appendChild(td);

        table.appendChild(tr);
    });

    document.getElementById("qg_items").innerHTML = '';
    if (nitems > 0)
	document.getElementById("qg_items").appendChild(table);

}


function add_edge_to_query_graph() {
    var n1 = document.getElementById("qg_edge_n1").value;
    var n2 = document.getElementById("qg_edge_n2").value;
    var et = document.getElementById("qg_edge_type").value;

    if (n1=='' || n2=='' || et=='') {
	document.getElementById("statusdiv").innerHTML = "<p class='error'>Please select two nodes and a valid edge type</p>";
	return;
    }

    document.getElementById("statusdiv").innerHTML = "<p>Added an edge of type <i>"+et+"</i></p>";
    var qgid = get_qg_id();

    if (et=='NONSPECIFIC') { et = null; }

    cyobj[999].add( {
	"data" : { "id"     : qgid,
		   "source" : n1,
		   "target" : n2,
		   "type"   : et,
		   "parentdivnum" : 999 }
    } );
    cylayout(999,"breadthfirst");

    var tmpdata = { "id"       : qgid,
		    "negated"  : null,
		    "relation" : null,
		    "source_id": n1,
		    "target_id": n2,
		    "type"     : et
		  };

    input_qg.edges.push(tmpdata);    
    display_query_graph_items();
}


function update_kg_edge_input() {
    document.getElementById("qg_edge_n1").innerHTML = '';
    document.getElementById("qg_edge_n2").innerHTML = '';

    var opt = document.createElement('option');
    opt.style.borderBottom = "1px solid black";
    opt.value = '';
    opt.innerHTML = "Source Node ("+input_qg.nodes.length+")&nbsp;&nbsp;&nbsp;&#8675;";
    document.getElementById("qg_edge_n1").appendChild(opt);

    opt = document.createElement('option');
    opt.style.borderBottom = "1px solid black";
    opt.value = '';
    opt.innerHTML = "Target Node ("+input_qg.nodes.length+")&nbsp;&nbsp;&nbsp;&#8675;";
    document.getElementById("qg_edge_n2").appendChild(opt);

    if (input_qg.nodes.length < 2) {
	opt = document.createElement('option');
	opt.value = '';
	opt.innerHTML = "Must have 2 nodes minimum";
	document.getElementById("qg_edge_n1").appendChild(opt);
	document.getElementById("qg_edge_n2").appendChild(opt.cloneNode(true));
	return;
    }

    input_qg.nodes.forEach(function(qgnode) {
	for (var x = 1; x <=2; x++) {
            opt = document.createElement('option');
	    opt.value = qgnode["id"];
	    opt.innerHTML = qgnode["curie"] ? qgnode["curie"] : qgnode["type"] ? qgnode["type"] : qgnode["id"];
	    document.getElementById("qg_edge_n"+x).appendChild(opt);
	}
    });
    get_possible_edges();
}

function get_possible_edges() {
    var qet_node = document.getElementById("qg_edge_type");
    qet_node.innerHTML = '';

    var opt = document.createElement('option');
    opt.style.borderBottom = "1px solid black";
    opt.value = '';
    opt.innerHTML = "Edge Type&nbsp;&nbsp;&nbsp;&#8675;";
    qet_node.appendChild(opt);

    var edge1 = document.getElementById("qg_edge_n1").value;
    var edge2 = document.getElementById("qg_edge_n2").value;

    if (!(edge1 && edge2) || (edge1 == edge2)) {
	opt = document.createElement('option');
	opt.value = '';
	opt.innerHTML = "Please select 2 different nodes";
	qet_node.appendChild(opt);
	return;
    }

    var nt1 = input_qg.nodes.filter(function(node){
	return node["id"] == edge1;
    });
    var nt2 = input_qg.nodes.filter(function(node){
	return node["id"] == edge2;
    });

    qet_node.innerHTML = '';
    opt = document.createElement('option');
    opt.style.borderBottom = "1px solid black";
    opt.value = '';
    opt.innerHTML = "Populating edges...";
    qet_node.appendChild(opt);

    if (nt1[0].type == null || nt2[0].type == null) {
	// NONSPECIFIC nodes only get NONSPECIFIC edges...for now
        qet_node.innerHTML = '';
        opt = document.createElement('option');
	opt.value = 'NONSPECIFIC';
	opt.innerHTML = "Unspecified/Non-specific";
	qet_node.appendChild(opt);
	return;
    }

    var relation = "A --> B";
    if (!(nt2[0].type in predicates[nt1[0].type])) {
	[nt1, nt2] = [nt2, nt1]; // swap
	relation = "B --> A";
    }

    if (nt2[0].type in predicates[nt1[0].type]) {
	if (predicates[nt1[0].type][nt2[0].type].length == 1) {
	    qet_node.innerHTML = '';
	    opt = document.createElement('option');
	    opt.value = predicates[nt1[0].type][nt2[0].type][0];
	    opt.innerHTML = predicates[nt1[0].type][nt2[0].type][0] + " ["+relation+"]";
	    qet_node.appendChild(opt);
	}
	else {
	    qet_node.innerHTML = '';
	    opt = document.createElement('option');
	    opt.style.borderBottom = "1px solid black";
	    opt.value = '';
            opt.innerHTML = "Edge Type ["+relation+"]&nbsp; ("+predicates[nt1[0].type][nt2[0].type].length+")&nbsp;&nbsp;&nbsp;&#8675;";
	    qet_node.appendChild(opt);

	    for (var pred of predicates[nt1[0].type][nt2[0].type]) {
		var opt = document.createElement('option');
		opt.value = pred;
		opt.innerHTML = pred;
		qet_node.appendChild(opt);
	    }

            opt = document.createElement('option');
	    opt.value = 'NONSPECIFIC';
	    opt.innerHTML = "Unspecified/Non-specific";
	    qet_node.appendChild(opt);
	}

    }
    else {
        qet_node.innerHTML = '';
	opt = document.createElement('option');
	opt.value = '';
	opt.innerHTML = "-- No edge types found --";
	qet_node.appendChild(opt);
    }
}


function add_nodeclass_to_query_graph(nodetype) {
    document.getElementById("allnodetypes").value = '';
    document.getElementById("allnodetypes").blur();

    if (nodetype.startsWith("LIST_"))
	add_nodelist_to_query_graph(nodetype);
    else
	add_nodetype_to_query_graph(nodetype);

    update_kg_edge_input();
    display_query_graph_items();
}


function add_nodetype_to_query_graph(nodetype) {
    document.getElementById("statusdiv").innerHTML = "<p>Added a node of type <i>"+nodetype+"</i></p>";
    var qgid = get_qg_id();

    var nt = nodetype;

    cyobj[999].add( {
        "data" : { "id"   : qgid,
		   "name" : nodetype+"s",
		   "type" : nt,
		   "parentdivnum" : 999 },
//        "position" : {x:100*qgid, y:50}
    } );
    cyobj[999].reset();
    cylayout(999,"breadthfirst");

    if (nodetype=='NONSPECIFIC') { nt = null; }
    var tmpdata = { "id"     : qgid,
		    "is_set" : null,
		    "name"   : null,
		    "desc"   : "Generic " + nodetype,
		    "curie"  : null,
		    "type"   : nt
		  };

    input_qg.nodes.push(tmpdata);
}

function add_nodelist_to_query_graph(nodetype) {
    var list = nodetype.split("LIST_")[1];

    document.getElementById("statusdiv").innerHTML = "<p>Added a set of nodes from list <i>"+list+"</i></p>";
    var qgid = get_qg_id();

    cyobj[999].add( {
        "data" : { "id"   : qgid,
		   "name" : nodetype,
		   "type" : "set",
		   "parentdivnum" : 999 }
    } );
    cyobj[999].reset();
    cylayout(999,"breadthfirst");

    var tmpdata = { "id"     : qgid,
		    "is_set" : true,
		    "name"   : nodetype,
		    "desc"   : "Set of nodes from list " + list,
		    "curie"  : null,
		    "type"   : null
		  };

    input_qg.nodes.push(tmpdata);
}


function enter_node(ele) {
    if (event.key === 'Enter')
	add_node_to_query_graph();
}

async function add_node_to_query_graph() {
    var thing = document.getElementById("newquerynode").value;
    document.getElementById("newquerynode").value = '';

    if (thing == '') {
        document.getElementById("statusdiv").innerHTML = "<p class='error'>Please enter a node value</p>";
	return;
    }

    var bestthing = await check_entity(thing);
    document.getElementById("devdiv").innerHTML +=  "-- best node = " + JSON.stringify(bestthing,null,2) + "<br>";

    if (bestthing.found) {
        document.getElementById("statusdiv").innerHTML = "<p>Found entity with name <b>"+bestthing.name+"</b> that best matches <i>"+thing+"</i> in our knowledge graph.</p>";
	sesame('openmax',statusdiv);

	var qgid = get_qg_id();

	cyobj[999].add( {
	    "data" : { "id"   : qgid,
		       "name" : bestthing.name,
		       "type" : bestthing.type,
		       "parentdivnum" : 999 },
	    //		"position" : {x:100*(qgid-nn), y:50+nn*50}
	} );

	var tmpdata = { "id"     : qgid,
			"is_set" : null,
			"name"   : bestthing.name,
			"curie"  : bestthing.curie,
			"type"   : bestthing.type
		      };

	document.getElementById("devdiv").innerHTML +=  "-- found a curie = " + bestthing.curie + "<br>";
	input_qg.nodes.push(tmpdata);

	cyobj[999].reset();
	cylayout(999,"breadthfirst");

	update_kg_edge_input();
	display_query_graph_items();
    }
    else {
        document.getElementById("statusdiv").innerHTML = "<p><span class='error'>" + thing + "</span> is not in our knowledge graph.</p>";
	sesame('openmax',statusdiv);
    }
}


function remove_edge_from_query_graph(edgeid) {
    cyobj[999].remove("#"+edgeid);

    input_qg.edges.forEach(function(result, index) {
	if (result["id"] == edgeid) {
	    //Remove from array
	    input_qg.edges.splice(index, 1);
	}
    });

    var idx = qgids.indexOf(edgeid);
    if (idx > -1)
	qgids.splice(idx, 1);

    display_query_graph_items();
}

function remove_node_from_query_graph(nodeid) {
    cyobj[999].remove("#"+nodeid);

    input_qg.nodes.forEach(function(result, index) {
	if (result["id"] == nodeid) {
	    //Remove from array
	    input_qg.nodes.splice(index, 1);
	}
    });

    var idx = qgids.indexOf(nodeid);
    if (idx > -1)
	qgids.splice(idx, 1);

    // remove items starting from end of array...
    for (var k = input_qg.edges.length - 1; k > -1; k--){
	if (input_qg.edges[k].source_id == nodeid) {
	    input_qg.edges.splice(k, 1);
	}
	else if (input_qg.edges[k].target_id == nodeid) {
	    input_qg.edges.splice(k, 1);
	}
    }

    update_kg_edge_input();
    display_query_graph_items();
}

function clear_qg(m) {
    if (cyobj[999]) { cyobj[999].elements().remove(); }
    input_qg = { "edges": [], "nodes": [] };
    update_kg_edge_input();
    get_possible_edges();
    display_query_graph_items();
    qgids = [];
    if (m==1){
	document.getElementById("statusdiv").innerHTML = "<p>Query Graph has been cleared.</p>";
    }
    document.getElementById('qg_form').style.visibility = 'visible';
    document.getElementById('qg_form').style.maxHeight = "100%";
}

function get_qg_id() {
    var new_id = 0;
    do {
	if (!qgids.includes("qg"+new_id))
	    break;
	new_id++;
    } while (new_id < 100);

    qgids.push("qg"+new_id);
    return "qg"+new_id;
}


function get_example_questions() {
    fetch(baseAPI + "api/rtx/v1/exampleQuestions")
        .then(response => response.json())
        .then(data => {
	    add_to_dev_info("EXAMPLE Qs",data);

	    var qqq = document.getElementById("qqq");
	    qqq.innerHTML = '';

            var opt = document.createElement('option');
	    opt.value = '';
	    opt.style.borderBottom = "1px solid black";
	    opt.innerHTML = "Example Questions&nbsp;&nbsp;&nbsp;&#8675;";
	    qqq.appendChild(opt);

	    for (var exq of data) {
		opt = document.createElement('option');
		opt.value = exq.question_text;
		opt.innerHTML = exq.query_type_id+": "+exq.question_text;
		qqq.appendChild(opt);
	    }
	})
        .catch(error => { //ignore...
	});
}


function load_nodes_and_predicates() {
    var allnodes_node = document.getElementById("allnodetypes");
    allnodes_node.innerHTML = '';

    fetch(baseAPI + "api/rtx/v1/predicates")
	.then(response => {
	    if (response.ok) return response.json();
	    else throw new Error('Something went wrong');
	})
        .then(data => {
	    add_to_dev_info("PREDICATES",data);
	    predicates = data;

	    var opt = document.createElement('option');
	    opt.value = '';
	    opt.style.borderBottom = "1px solid black";
	    opt.innerHTML = "Add Node by Type&nbsp;&nbsp;&nbsp;&#8675;";
	    allnodes_node.appendChild(opt);

            for (const p in predicates) {
		opt = document.createElement('option');
		opt.value = p;
		opt.innerHTML = p;
		allnodes_node.appendChild(opt);
	    }
            opt = document.createElement('option');
	    opt.value = 'NONSPECIFIC';
	    opt.innerHTML = "Unspecified/Non-specific";
	    allnodes_node.appendChild(opt);

            opt = document.createElement('option');
	    opt.id = 'nodesetA';
	    opt.value = 'LIST_A';
	    opt.title = "Set of Nodes from List [A]";
	    opt.innerHTML = "List [A]";
	    allnodes_node.appendChild(opt);

            opt = document.createElement('option');
	    opt.id = 'nodesetB';
	    opt.value = 'LIST_B';
            opt.title = "Set of Nodes from List [B]";
	    opt.innerHTML = "List [B]";
	    allnodes_node.appendChild(opt);
	})
        .catch(error => {
	    var opt = document.createElement('option');
	    opt.value = '';
	    opt.style.borderBottom = "1px solid black";
	    opt.innerHTML = "-- Error Loading Node Types --";
	    allnodes_node.appendChild(opt);
        });
}


function add_to_dev_info(title,jobj) {
    var dev = document.getElementById("devdiv");
    dev.appendChild(document.createElement("br"));
    dev.appendChild(document.createTextNode('='.repeat(80)+" "+title+"::"));
    var pre = document.createElement("pre");
    //pre.id = "responseJSON";
    pre.appendChild(document.createTextNode(JSON.stringify(jobj,null,2)));
    dev.appendChild(pre);
}


function togglecolor(obj,tid) {
    var col = '#888';
    if (obj.checked == true) {
	col = '#047';
    }
    document.getElementById(tid).style.color = col;
}


// adapted from http://www.activsoftware.com/
function getQueryVariable(variable) {
    for (var qsv of window.location.search.substring(1).split("&")) {
	var pair = qsv.split("=");
	if (decodeURIComponent(pair[0]) == variable)
	    return decodeURIComponent(pair[1]);
    }
    return false;
}

// LIST FUNCTIONS
var entities  = {};
var listItems = {};
listItems['A'] = {};
listItems['B'] = {};
listItems['SESSION'] = {};
var numquery = 0;

function display_list(listId) {
    if (listId == 'SESSION') {
	display_session();
	return;
    }
    var listhtml = '';
    var numitems = 0;

    for (var li in listItems[listId]) {
	if (listItems[listId].hasOwnProperty(li)) { // && listItems[listId][li] == 1) {
	    numitems++;
	    listhtml += "<tr class='hoverable'>";

	    if (entities.hasOwnProperty(li)) {
		listhtml += "<td>"+entities[li].checkHTML+"</td>";
		listhtml += "<td>"+entities[li].name+"</td>";
		listhtml += "<td>"+entities[li].curie+"</td>";
		listhtml += "<td>"+entities[li].type+"</td>";
	    }
	    else {
		listhtml += "<td id='list"+listId+"_entitycheck_"+li+"'>--</td>";
		listhtml += "<td id='list"+listId+"_entityname_"+li+"'>"+li+"</td>";
		listhtml += "<td id='list"+listId+"_entitycurie_"+li+"'>looking up...</td>";
		listhtml += "<td id='list"+listId+"_entitytype_"+li+"'>looking up...</td>";
		entities[li] = {};
		entities[li].checkHTML = '--';
	    }

	    listhtml += "<td><a href='javascript:remove_item(\"" + listId + "\",\""+ li +"\");'/> Remove </a></td></tr>";
	}
    }


    document.getElementById("numlistitems"+listId).innerHTML = numitems;
    document.getElementById("menunumlistitems"+listId).innerHTML = numitems;

    if (document.getElementById("nodeset"+listId))
	document.getElementById("nodeset"+listId).innerHTML = "List [" + listId + "] -- (" + numitems + " items)";

    if (numitems > 0) {
	listhtml = "<table class='sumtab'><tr><th></th><th>Name</th><th>Item</th><th>Type</th><th>Action</th></tr>" + listhtml + "</table><br><br>";
	document.getElementById("menunumlistitems"+listId).classList.add("numnew");
	document.getElementById("menunumlistitems"+listId).classList.remove("numold");
    }
    else {
	document.getElementById("menunumlistitems"+listId).classList.remove("numnew");
	document.getElementById("menunumlistitems"+listId).classList.add("numold");
    }

    listhtml = "Items in this list can be passed as input to queries that support list input, by specifying <b>["+listId+"]</b> as a query parameter.<br><br>" + listhtml + "<hr>Enter new list item or items (space and/or comma-separated; use &quot;double quotes&quot; for multi-word items):<br><input type='text' class='questionBox' id='newlistitem"+listId+"' onkeydown='enter_item(this, \""+listId+"\");' value='' size='60'><input type='button' class='questionBox button' name='action' value='Add' onClick='javascript:add_new_to_list(\""+listId+"\");'/>";

//    listhtml += "<hr>Enter new list item or items (space and/or comma-separated):<br><input type='text' class='questionBox' id='newlistitem"+listId+"' value='' size='60'><input type='button' class='questionBox button' name='action' value='Add' onClick='javascript:add_new_to_list(\""+listId+"\");'/>";

    if (numitems > 0)
    	listhtml += "<a style='margin-left:20px;' href='javascript:delete_list(\""+listId+"\");'/> Delete List </a>";

    listhtml += "<br><br>";

    document.getElementById("listdiv"+listId).innerHTML = listhtml;
    check_entities();
}

function get_list_as_string(listId) {
    var liststring = '[';
    var comma = '';
    for (var li in listItems[listId]) {
	if (listItems[listId].hasOwnProperty(li) && listItems[listId][li] == 1) {
	    liststring += comma + li;
	    comma = ',';
	}
    }
    liststring += ']';
    return liststring;
}


function get_list_as_curie_array(listId) {
    var carr = [];
    for (var li in listItems[listId])
	if (listItems[listId].hasOwnProperty(li) && listItems[listId][li] == 1)
	    carr.push(entities[li].curie);

    return carr;
}


function add_items_to_list(listId,indx) {
    for (var nitem in columnlist[indx])
	if (columnlist[indx][nitem]) {
            nitem = nitem.replace(/['"]+/g,''); // remove all manner of quotes
	    listItems[listId][nitem] = 1;
	}
    display_list(listId);
}

function enter_item(ele, listId) {
    if (event.key === 'Enter')
	add_new_to_list(listId);
}

function add_new_to_list(listId) {
    //var itemarr = document.getElementById("newlistitem"+listId).value.split(/[\t ,]/);
    var itemarr = document.getElementById("newlistitem"+listId).value.match(/\w+|"[^"]+"/g);

    document.getElementById("newlistitem"+listId).value = '';
    for (var item in itemarr) {
	itemarr[item] = itemarr[item].replace(/['"]+/g,''); // remove all manner of quotes
        //console.log("=================== item:"+itemarr[item]);
	if (itemarr[item]) {
	    listItems[listId][itemarr[item]] = 1;
	}
    }
    display_list(listId);
    add_to_dev_info("ALL_ENTITIES:",entities);
}

function remove_item(listId,item) {
    delete listItems[listId][item];
    display_list(listId);
}

function delete_list(listId) {
    listItems[listId] = {};
    display_list(listId);
}


function check_entities() {
    for (let entity in entities) {
	if (entities[entity].checkHTML != '--') continue;

	fetch(baseAPI + "api/rtx/v1/entity/" + entity)
	    .then(response => response.json())
	    .then(data => {
                add_to_dev_info("ENTITIES:"+entity,data);

		if (data.curie) {
		    entities[entity].curie = data.curie;
		    entities[entity].name  = data.name;
		    entities[entity].type  = data.type;
		    //entities[entity].name = data.name.replace(/['"]/g, '&apos;');  // might need this?

		    entities[entity].isvalid   = true;
		    entities[entity].checkHTML = "<span class='explevel p9'>&check;</span>&nbsp;";
		    document.getElementById("devdiv").innerHTML += data.type+"<br>";
		}
		else {
		    entities[entity].curie = "<span class='error'>unknown</span>";
		    entities[entity].name  = entity;
		    entities[entity].type  = "<span class='error'>unknown</span>";
		    entities[entity].isvalid   = false;
		    entities[entity].checkHTML = "<span class='explevel p1'>&cross;</span>&nbsp;";
		}

		// in case of a 404...?? entstr = "<span class='explevel p0'>&quest;</span>&nbsp;n/a";

		for (var elem of document.querySelectorAll("[id$='_entitycurie_"+entity+"']"))
		    elem.innerHTML = entities[entity].curie;
		for (var elem of document.querySelectorAll("[id$='_entityname_"+entity+"']"))
		    elem.innerHTML = entities[entity].name;
		for (var elem of document.querySelectorAll("[id$='_entitytype_"+entity+"']"))
		    elem.innerHTML = entities[entity].type;
		for (var elem of document.querySelectorAll("[id$='_entitycheck_"+entity+"']"))
		    elem.innerHTML = entities[entity].checkHTML;

	    })
	    .catch(error => {
                add_to_dev_info("ENTITIES(error):"+entity,error);
		entities[entity].name = "n/a";
		entities[entity].type = "n/a";
                entities[entity].isvalid   = false;
		entities[entity].checkHTML = "<span class='explevel p0'>&quest;</span>&nbsp;";
                for (var elem of document.querySelectorAll("[id$='_entityname_"+entity+"']"))
		    elem.innerHTML = entities[entity].name;
                for (var elem of document.querySelectorAll("[id$='_entitytype_"+entity+"']"))
		    elem.innerHTML = entities[entity].typecheckHTML;
                for (var elem of document.querySelectorAll("[id$='_entitycheck_"+entity+"']"))
		    elem.innerHTML = entities[entity].checkHTML;

	    });
    }
}


async function check_entity(term) {
    var data;
    var ent = {};
    ent.found = false;

    if (entities[term]) {
        if (!entities[term].isvalid)
            return ent; // contains found=false

	data = entities[term];
    }
    else {
	var response = await fetch(baseAPI + "api/rtx/v1/entity/" + term);
	data = await response.json();

	add_to_dev_info("ENTITY:"+term,data);
	if (!data.curie)
	    return ent; // contains found=false
    }

    ent.found = true;
    ent.curie = data.curie;
    ent.name  = data.name;
    ent.type  = data.type;

    if (!entities[data.curie]) {
	entities[data.curie] = {}; //xob[i].name + "::" + xob[i].type;
	entities[data.curie].curie = data.curie;
	entities[data.curie].name  = data.name;
	entities[data.curie].type  = data.type;
        entities[data.curie].isvalid   = true;
	entities[data.curie].checkHTML = "<span class='explevel p9'>&check;</span>&nbsp;";
    }

    return ent;
}


function add_to_session(resp_id,text) {
    numquery++;
    listItems['SESSION'][numquery] = resp_id;
    listItems['SESSION']["qtext_"+numquery] = text;
    display_session();
}

function display_session() {
    var listId = 'SESSION';
    var listhtml = '';
    var numitems = 0;

    for (var li in listItems[listId]) {
        if (listItems[listId].hasOwnProperty(li) && !li.startsWith("qtext_")) {
            numitems++;
            listhtml += "<tr><td>"+li+".</td><td><a target='_new' title='view this message in a new window' href='//"+ window.location.hostname + window.location.pathname + "?m="+listItems[listId][li]+"'>" + listItems['SESSION']["qtext_"+li] + "</a></td><td><a href='javascript:remove_item(\"" + listId + "\",\""+ li +"\");'/> Remove </a></td></tr>";
        }
    }
    if (numitems > 0) {
        listhtml += "<tr style='background-color:unset;'><td style='border-bottom:0;'></td><td style='border-bottom:0;'></td><td style='border-bottom:0;'><a href='javascript:delete_list(\""+listId+"\");'/> Delete Session History </a></td></tr>";
    }


    if (numitems == 0) {
        listhtml = "<br>Your query history will be displayed here. It can be edited or re-set.<br><br>";
    }
    else {
        listhtml = "<table class='sumtab'><tr><th></th><th>Query</th><th>Action</th></tr>" + listhtml + "</table><br><br>";
    }

    document.getElementById("numlistitems"+listId).innerHTML = numitems;
    document.getElementById("menunumlistitems"+listId).innerHTML = numitems;
    document.getElementById("listdiv"+listId).innerHTML = listhtml;
}


function copyJSON(ele) {
    var containerid = "responseJSON";

    if (document.selection) {
	var range = document.body.createTextRange();
	range.moveToElementText(document.getElementById(containerid));
	range.select().createTextRange();
	document.execCommand("copy");
	addCheckBox(ele);
    }
    else if (window.getSelection) {
	var range = document.createRange();
	range.selectNode(document.getElementById(containerid));
        window.getSelection().removeAllRanges();
	window.getSelection().addRange(range);
	document.execCommand("copy");
	addCheckBox(ele);
	//alert("text copied")
    }
}

function copyTSVToClipboard(ele) {
    var dummy = document.createElement("textarea");
    document.body.appendChild(dummy);
    dummy.setAttribute("id", "dummy_id");
    for (var line of summary_tsv)
	document.getElementById("dummy_id").value+=line+"\n";
    dummy.select();
    document.execCommand("copy");
    document.body.removeChild(dummy);

    addCheckBox(ele);
}

function addCheckBox(ele) {
    var check = document.createElement("span");
    check.className = 'explevel p9';
    check.innerHTML = '&check;';
    ele.parentNode.insertBefore(check, ele.nextSibling);

    var timeout = setTimeout(function() { check.remove(); }, 1500 );
}
