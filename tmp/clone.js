
var hosts = _HOST;
var msg_proce     = "<span style=color:red>æ­£åœ¨æäº¤æ•°æ®...</span>";
var msg_success   = "<span style=color:red>ä¿å­˜æˆåŠŸ</span>";
var rowsremark    = _ARGV.rowsremark.split(",");
var rowsremark_pinyin  = _ARGV.rowsremark_pinyin.split(",");
var lasthosts     = [];	//æœ€åŽæŠ¥è­¦æœåŠ¡å™¨ID
var lasthostshash = 0;	//æœ€åŽæŠ¥è­¦æœåŠ¡å™¨å“ˆå¸ŒID
var lasthostid    = 0;	//æœ€åŽæŸ¥çœ‹çš„æœåŠ¡å™¨
var lastorderid   = 0;	//æœ€åŽæŠ¥è­¦çš„è®¢å•
var lastpage      = 0;	//æœ€åŽç¿»é¡µä½ç½®
var windowfocus   = 0;	//çª—å£æ˜¯å¦èšç„¦
for(var i=0;i<rowsremark.length;i++){
	rowsremark[i] = {name:rowsremark[i],pinyin:rowsremark_pinyin[i]};
}
function g_h_i(hostid){ var rs = $.find_row(hosts,'hostid',hostid);return rs?rs:{hostid:hostid,hostname:'è¯¥æœåŠ¡å™¨å·²ç»è¢«åˆ é™¤'};}
function UserLoginCheck(){
	if(_LOGIN_OK){
		return true;
	}else{
		alert("æ‚¨éœ€ç™»å½•æ‰èƒ½è¿›è¡Œè¯¥æ“ä½œ");
		return false;
	}
}
function u_s_save(input,call){
	var $this = $(input);
	var name  = $this.attr("name");
	var offset= $this.is(":hidden")?$this.parent().offset():$this.offset();
	var val   = $this.is("[type=checkbox]")?($this.prop("checked")?$this.val():"0"):$this.val();
	$.layer("showdiv")
		.html(msg_proce)
		.show()
		.css({left:offset.left+50,top:offset.top});
	$.getJSON("?action=coin.setting&name="+name+"&value="+val,function(d){
		if(d.errno==0){
			$.layer("showdiv").html(msg_success).fadeOut(1500);
			if(call) call();
		}else{
			$.layer("showdiv").hide();
			alert(d.error);
		}
	});
}
function is_pc_page() {
	return $("#gameid option[value=10]").length!=0;
}
//ä¿®æ”¹æ›´æ–°
function game_change(select){
	var gameid = $(select).val();
	var _hosts = [];
	if (is_pc_page()){
		_hosts.push({hostid:'maxprice',hostname:'|--æœ€é«˜ä»·æ”¶è´§/æœ€ä½Žä»·å‡ºè´§'});
    }
	$.merge(_hosts,$.grep(hosts,function(h){
		return h.gameid == gameid;
	}));
	$(select).closest('form').find('[name=hostid]').fill_select(_hosts,{text:'hostname',value:'hostid'},'è¯·é€‰æ‹©åŽè¿›è¡Œäº¤æ˜“').trigger('change');
	$.cookie("C_GAMEID",gameid);
}
function host_change(select){
	if(add_new(select)){
	}else if($(select).val()=='maxprice'){
		$("#layer_showhost").trigger("autorise").html("æ­£åœ¨ä¸‹è½½æŽ’è¡Œæ•°æ®....").load("?action=showgamesort&gameid="+$(select).closest('form').find('[name=gameid]').val()+"&sort=maxprice");
	}else if($(select).val()!=''){
		u_h_view($(select).val());
	}
}
//å…³æ³¨æ“ä½œ
function u_c_add(hostid){
	if(!UserLoginCheck()){
		return false;
	}else{
		u_c_exec({action:"coin.coinadd",hostid:hostid});
	}
}
function u_c_set(hostid,name,value){
	if(!UserLoginCheck()){
		return false;
	}else{
		u_c_exec({action:"coin.coinset",hostid:hostid,name:name,value:value},1);
	}
}
function u_c_all(name,value,option){
	if(!UserLoginCheck()){
		return false;
	}else{
		u_c_exec({action:"coin.coinall",name:name,value:value,option:option});
	}
}
function u_c_del(hostid){
	if(!UserLoginCheck()){
		return false;
	}else{
		u_c_exec({action:"coin.coindel",hostid:hostid});
	}
}
function u_c_exec(data,deload){
	$.post("?",data,function(rs){
		if(rs.errno == 0){
			$.layer("showdiv").html(msg_success).fadeOut(1000);
			if(!deload) u_c_list();
		}else{
			alert(rs.error);
		}
	},"json");
}
function u_c_next(hostid,offset){
	if($("#data_0").next().is(".data")==0){
		alert("ä½ è¿˜æœªæ·»åŠ æœåŠ¡å™¨è¿›å…¥æ¯”ä»·å™¨å³ä¾§çš„åº“å­˜è¡¨");
	}else{
		if(offset == 1){
			$tr = $("#data_"+hostid).removeClass("select").next();
			if(!$tr.is("#coinlist tr.data:not(#data_0)")){
				$tr = $("#coinlist tr.data:not(#data_0):first");
			}
		}else{
			$tr = $("#data_"+hostid).removeClass("select").prev();
			if(!$tr.is("#coinlist tr.data:not(#data_0)")){
				$tr = $("#coinlist tr.data:not(#data_0):last");
			}
		}
		u_h_view($tr.addClass("select").attr("hostid"));
	}
}
function u_c_list(page){
	lastpage = page?page:lastpage;
	lasthosts     = [];
	lasthostshash = 0;
	var d    = {page:lastpage,pagerule:$("#pagerule").val()};
	$("#coinlist").html("æ­£åœ¨åŠ è½½åˆ—è¡¨").load("?action=coin.coinlist&index=1",d,function(d){
		$("#fasthostname").autocomplete({
			minLength: 1,
			source: function(request, response) {
				$.getJSON("?action=game.jsonhost&autocomplete=1&limit=20",{keyword:request.term},function(data){
					if(data.length==0){
						$(this).closest(".data").attr("hostid",0);
					}else if(data.length==1){
						$("#fasthostname").closest(".data").attr("hostid",data[0].hostid);
						$("#fasthostname").trigger("coindetail");
						data = [];
					}
					response(data);
				});
			},
			select:function(e,ui){
				$("#fasthostname").closest(".data").attr("hostid",ui.item.hostid);
				$("#fasthostname").trigger("coindetail");
			}
		}).bind("coindetail",function(){
			var $tr = $(this).closest(".data");
			$.getJSON("?action=coin.coinjson&hostid="+$tr.attr("hostid"),function(d){
				if(d.errno==1){
					$("[name=quantity]",$tr).val("");
					$("[name=oldquantity]",$tr).val(0);
					$("[name=avgprice]",$tr).html(0);
				}else{
					$("[name=quantity]",$tr).val($.intval(d.quantity));
					$("[name=oldquantity]",$tr).val($.intval(d.quantity));
					$("[name=avgprice]",$tr).html($.floatval(d.avgprice)).next().hide();
				}
			});
		});
		$("#spanrows").html($("#coinrows").html());
		$("#spanshowpage").html($("#coinshowpage").html());
		$("#showgameid").change(function(){
			$.getJSON("?action=coin.showset&name=showgameid&value="+$(this).val(),function(d){
				u_c_list();
				$.layer("showdiv").html(msg_success).fadeOut(1500);
			});
		});
	});
}
function u_c_import(source){
	var $form    = $("#import");
	var querystr = "&source="+source+"&gamecode="+$(":input[name=gamecode]:checked").val()+"&clean="+($("[name=clean]").attr("checked")?1:0);
	if(source=='clipboard'){
		if(window.clipboardData.getData("text") == ""){
			return alert("è¯·å…ˆå¤åˆ¶æœåŠ¡å™¨åˆ—è¡¨");
		}else if(window.clipboardData.getData("text").match(/(æŠ¥è­¦é‡|å‡ä»·|å¤‡å¿˜)/)){
			return alert("è‹¥è¦å¯¼å…¥æŠ¥è­¦é‡ã€åº“å­˜å‡ä»·ã€å¤‡å¿˜ï¼Œè¯·é‡‡ç”¨ä¸Šä¼ Excelçš„æ–¹å¼å¯¼å…¥ï¼Œæ ‡é¢˜å¤„è¯·æ³¨æ˜Žè¯¥åˆ—å†…å®¹ï¼šæœåŠ¡å™¨åç§°ã€æŠ¥è­¦ä»·ã€åº“å­˜é‡ã€æŠ¥è­¦é‡ã€åº“å­˜å‡ä»·ã€å¤‡å¿˜");
		}
	}else{
		if($("#fileupload").val()==""){
			return alert("è¯·é€‰æ‹©ä¸Šä¼ æ–‡ä»¶");
		}
	}
	if($("[name=clean]").prop("checked") && !confirm('ç»§ç»­å¯¼å…¥ä¼šåˆ é™¤å½“å‰æœåŠ¡å™¨åˆ—è¡¨åœ¨æœ¬æ¬¡å¯¼å…¥ä¸å­˜åœ¨çš„æœåŠ¡å™¨')){
		return ;
	}
	if(source=='clipboard'){
		$.post("?action=coin.import"+querystr,{"data":window.clipboardData.getData("text")},function(d){
			if(d.errno==0){
				u_c_list();
			}else{
				alert(d.error);
			}
		},"json");
	}else{
		$form.attr("action","?action=coin.import"+querystr);
		$form.submit();
	}
}
//è¿‡æ»¤
function u_f_add(id,type){
	if(!UserLoginCheck()){
		return false;
	}else{
		u_f_exec({action:"coin.filteradd",siteid:id,userid:id,type:type});
	}
}
function u_f_del(id,type){
	if(!UserLoginCheck()){
		return false;
	}else{
		u_f_exec({action:"coin.filterdel",siteid:id,userid:id,type:type});
	}
}
function u_f_exec(data,deload){
	$.post("?",data,function(rs){
		if(rs.errno == 0){
			$.layer("showdiv").html(msg_success).fadeOut(1000);
			if(!deload) u_f_list();
			u_h_view(lasthostid);
		}else{
			alert(rs.error);
		}
	},"json");
}
function u_f_list(page){
	$("#filter>div").load("?action=coin.filterlist");
}
function u_g_save(f){
	$.post("?action=coin.gamesave",$(f).serialize(),function(d){
		if(d.errno==0){
			u_c_list();
			u_g_list();
		}else{
			alert(d.error);
		}
	},'json');
}
function u_g_list(page){
	$("#game").load("?action=coin.gamelist");
}
function u_d_prompt(reset){
	if(!_LOGIN_OK) return true;
	if($("tr.data:first").length>0) {
		$.getScript(_HTTP_PATH+"/jq/i-"+_ARGV.loginuid+"-"+_ARGV.loginukey,function(){
			if(data.cartcount > 0) {
				$(window).unbind("unload");
				window.location.href = '/?action=valet.ordersell';
			}
			if(data.orderid > lastorderid){
				$(window).unbind("unload");
				window.location.reload();
			}
			if(data.ordercount > 0){

			}else{
				//æ²¡æœ‰æŠ¥è­¦æœåŠ¡å™¨ï¼Œåœæ­¢æŠ¥è­¦
				if(data.hosts.length==0){
					$('#jquery_jplayer').jPlayer('stop');
				//æœ‰æŠ¥è­¦æœåŠ¡å™¨ï¼Œå¼€å¯æŠ¥è­¦
				}else{
					if($("#pop").prop("checked") && windowfocus == 0){windowfocus = 1;window.focus();}
					if($("#sound").prop("checked")) $('#jquery_jplayer').jPlayer('play');
					else $('#jquery_jplayer').jPlayer('stop');
				}
				var hostshash = 0;		//æŠ¥è­¦æœåŠ¡å™¨å“ˆè¥¿
				var hostsmain = [];		//äº¤å‰çš„æŠ¥è­¦æœåŠ¡å™¨
				var hostshtml = "";
				$.each(data.hosts,function(i,v){
					hostshash += v<<2;
				});
				if(reset || lasthostshash != hostshash){
					$.each(lasthosts,function(i,v){
						if($.inArray(v,data.hosts)!=-1) hostsmain.push(v);
					});
					$.each(lasthosts,function(i,v){
						if($.inArray(v,hostsmain)==-1) $("#data_"+v).removeClass("prompt");
					});
					$.each(data.hosts,function(i,v){
						var _h = g_h_i(v);
						if($.inArray(v,hostsmain)==-1) $("#data_"+v).addClass("prompt");
						if(i<30){
							hostshtml += "<div style=width:48%;float:left;margin-top:5px; ><a href=#host_"+_h.hostid+" onclick=setTimeout(function(){u_h_view("+_h.hostid+");},100)>"+_h.hostname+"</a></div>";
						}
					});
					$.message_box({ title:"å½“å‰å…±æœ‰ <span style=color:red>"+data.hosts.length+"</span> ä¸ªæŠ¥è­¦æœåŠ¡å™¨<a href='#stock'>åŽ»åº“å­˜è¡¨â†‘</a>/<a href='#top'>åŽ»é€ŸæŸ¥â†‘</a>",message:hostshtml});
					lasthosts     = data.hosts;
					lasthostshash = hostshash;
				}
			}
		},"json");
	}
}

function u_h_view(hostid,args){
	var $layer = $("#layer_showhost")
		.html("ä¸‹è½½ä¸­...è‹¥ç½‘é€Ÿæ…¢è¯·æ¢ç”¨<a href='http://www1.bijiaqi.com' target='_blank' style='color:blue'>www1.bijiaqi.com</a>")
		.trigger("autorise");
		if($("#hostid").val() != hostid){
			var _h   = g_h_i(hostid);
			if(_h.gameid != $("#gameid").val())$("#gameid").val(_h.gameid).trigger("change");
			$("#hostid").val(_h.hostid).trigger("change");
		}
		$.getScript(_HTTP_PATH+"/jq/s-"+(lasthostid = hostid)+"-"+($.cookie("C_S_STOCK")=="1"?1:0)+"-"+_ARGV.tsid,function(){
            $layer.trigger('loaded');
			if($("#filter :input[name=filtershow]:checked").val() == "0"){
				$("#layer_showhost .bijia tr.tb_filter").hide();
			}
			if($("#newcount").length>0){
				$("#jquery_jplayer1").jPlayer("setFile",'/statics/sounds/order_auto.mp3').jPlayer('play');
				$("#dialog").html("<span style=font-size:15px;color:red>æ‚¨æœ‰æ–°çš„è‡ªåŠ¨ä¸‹å•è®¢å•,<a href=?action=valet.ordersell>ç‚¹æ­¤æŸ¥çœ‹</a></span>").dialog('option',{width: 400,title:'è®¢å•æé†’',position:'center'}).dialog('open');
			}
		});
}

//ä¿®æ”¹éœ€æ±‚
function v_n_p(d,needid){
	$("<input type=text name=test size=3 />")
		.insertAfter($(d).hide())
		.val($.trim($(d).text()))
		.bind({"keydown":function(e){
			if(e.keyCode==13 || e.keyCode==32){
				$(this).trigger("save").unbind("blur");
			}
		},"save":function(){
			var _this = this;
			$.get("?action=valet.needsave",{name:$(d).attr("name"),value:$(_this).val(),needid:needid});
			setTimeout(function(){
				$(_this).prev().text($(_this).val()).show();
				$(_this).remove();
			},1000);
		},"blur":function(){
			var _this = this;
			if(confirm('ç¡®è®¤ä¿®æ”¹'+($(d).attr("name")=="price"?"ä»·æ ¼":"æ•°é‡")+'å—')){
				$(_this).trigger("save");
			}else{
				$(_this).prev().show();
				$(_this).remove();
			}
		}}).focus();
}
//åŽ†å²æ•°æ®
function doListLogs(hostid){
	$("#logs").html("æ­£åœ¨ä¸‹è½½åŽ†å²æ•°æ®....").load("?action=showlogs&hostid="+(lasthostid = hostid),function(){
		$("#logstr").show();
	});
}
//ç½‘ç«™æŽ’è¡Œ
function l_s_h(){
	$("#layer_showhost").trigger("autorise").html("æ­£åœ¨ä¸‹è½½ç½‘ç«™ç‚¹å‡»æŽ’è¡Œæ•°æ®....").load("?action=showsitehits");
}
//ä¸»æœºæŽ’è¡Œ
function l_h_h(){
	$("#layer_showhost").trigger("autorise").html("æ­£åœ¨ä¸‹è½½ç½‘ç«™ç‚¹å‡»æŽ’è¡Œæ•°æ®....").load("?action=showhosthits");
}
$(function(){
	u_c_list();
	if(_LOGIN_OK){
		setInterval('u_d_prompt()',6000);
	}
	//æœåŠ¡å™¨è‡ªåŠ¨å®Œæˆ
	$('#speedhostname').autocomplete({
		minLength: 1,
		source: function(request, response) {
			$.getJSON("?action=game.jsonhost&autocomplete=1&limit=20",{keyword:request.term},function(data){
				if(data.length==1){
					$("#gameid").val(data[0].gameid).trigger("change");
					$("#hostid").val(data[0].hostid).trigger("change");
					data = [];
				}
				response( data );
			});
		},
		select:function(e,ui){
			$("#gameid").val(ui.item.gameid).trigger("change");
			$("#hostid").val(ui.item.hostid).trigger("change");
		}
	}).mouseover(function(){
		var $el = $("#hostid");
		$el.css("width", $el.data("origWidth"));
	});
	//åº“å­˜ä¸‹å•é¢„å¤„ç†
	$("#stockquick").on("keyup","input",function(){
		if(!$(this).is("[name=msg]") && $(this).val().match(/[^0-9\.]/)){
			$(this).val($(this).val().replace(/[^0-9\.]/g,''));
		}
	//å¤åˆ¶å†…å®¹
	}).find("a.copy").copy({
		"before":function(){
			var $sq  = $("#stockquick");
			var data = null;
			if($("table.kucun").length==0){
				alert("ä½ é‚£è¿˜æœªé€‰æ‹©æœåŠ¡å™¨");
			}else if($("input[name=quantity]",$sq).val()=='' || $("input[name=price]",$sq).val()==''){
				alert("æ‚¨è¿˜æœªè¾“å…¥æ•°é‡å’Œä»·æ ¼");
			}else{
				data = {
					"æ¸¸æˆ":$("#gameid option:selected").text(),
					"æœåŠ¡å™¨":$("#hostid option:selected").text(),
					"å•ä½":$("table.kucun").attr("game-unit"),
					"æ•°é‡":$("input[name=quantity]",$sq).val(),
					"ä»·æ ¼":$("input[name=price]",$sq).val()
				};
				$(this).attr("_val",$("[name=msg]",$sq).val().replace(/\[([^\]]+)\]/g,function($0,$1){
					return data[$1]?data[$1]:'';
				}));
			}
		}
	});
	//æœåŠ¡å™¨æ˜¾ç¤º
	$("#layer_showhost").on("autorise",function(e){
		var _h = $(document).scrollTop()-$("#layer_showhost_height").offset().top;
		if(_h>0){
			$("#layer_showhost_height").height(_h);
		}else{
			$("#layer_showhost_height").height(0);
		}
	}).on("click","a.orderadd",function(){
		var params   = "";
		var bidprice = $(this).closest("tr").find("[name='bidprice']").val();
		if(bidprice.match(/^[0-9]/)){
			params  += "&bidprice="+bidprice;
		}else if($("#stockquick [name=price]").val()!=''){
			params  += "&bidprice="+$("#stockquick [name=price]").val();
		}
		if($("#stockquick [name=quantity]").val()!=''){
			params  += "&quantity="+$("#stockquick [name=quantity]").val();
		}
		$(this).attr("href",$(this).attr("data-url")+params);
	});
    (function(){
        var $layer = $("#layer_showhost");
        $layer.on({
            'click':function(){
                $(this).trigger('limit');
            },'limit':function(){
                var $table = $(this).closest("table.limit");
                var limit  = $table.attr('data-limit') || 8;
                if($(this).data('hide')){
                    $(this).data('hide',false).find("td").text("åªæ˜¾ç¤ºå‰"+limit+"æ¡æ•°æ®<<<");
                    $(".row",$table).show();
                }else{
                    $(this).data('hide',true).find("td").text("æ˜¾ç¤ºå…¨éƒ¨æ•°æ®>>>");
                    $(".row:gt("+(limit-1)+")",$table).hide();
                }
                return false;
            }
        },'.more').on('loaded',function(){
            $(this).find("tr.more").trigger("limit");
        });
    })();
	//æœåŠ¡å™¨é€ŸæŸ¥ é€‰æ‹©æ¸¸æˆ  //æ¸¸æˆé€‰æ‹©
	$("#speedsearch").bind({"setGame":function(e,gameID){
        if(window.location.href.indexOf('mobile')===-1){
            //ä¿å­˜æ¸¸æˆIDåˆ°COOKIE
            $.cookie("C_S_GAMEID",gameID);
            $("#speedsearch_gameid").val(gameID);
            $("#speedsearch_gamename").html('<a href="#" val="'+(gameID)+':">'+$("#gameid option[value="+gameID.split(":")[0]+"]").text()+'</a>');
        }else{
            $.cookie("C_S_GAMEID",gameID);
            $("#speedsearch_gameid").val(gameID);
            $("#speedsearch_gamename").html('<a href="#" val="'+(gameID)+':">'+$("#gameid option[value="+gameID.split(":")[0]+"]").text()+'</a>');
        }
		return this;
	//æ˜¾ç¤ºæœåŠ¡å™¨
	},"showServer":function(e){
		if($("#speedsearch_char td.focus").text().indexOf("éš")!=-1 || $("#speedsearch_char td.focus").length==0){
			$("#speedsearch_result").html("");
		}else{
			var _s = new $.str_buffer("");
			var _o = $("#speedsearch_gameid").val().split(":");
			var _b = $.trim($("#speedsearch_char td.focus").text().replace(/\W+/,''));
			if(_o.length==1) _o[1] = "";
			$.each(hosts,function(t,b){
				if(_o[0] == b.gameid && (_o[1]=="" || b.language==_o[1]) && (_b=="" || _b==b.hostname.substring(0,1))){
					_s.add("<div class=\"list\"><div class=\"name\" onclick=\"u_h_view("+b.hostid+")\"><a href=\"javascript:void(0)\">"+(b.hostname.length>32?b.hostname.substr(0,29)+"..":b.hostname)+"</a></div><div class=\"option\"><a href=\"javascript:void(u_c_add("+b.hostid+"))\" class=\"login\">åŠ åˆ°åº“å­˜è¡¨</a></div></div>");
				}
			});
			$("#speedsearch_result").show().html(_s.to_string());
		}
	}}).delegate("#speedsearch_game a",{click:function(e,noload){
		$("#speedsearch_game a.focus").not($(this).addClass("focus")).removeClass("focus");
		if($(this).is("[val=other]")){
			if(!noload){
				$(this).select_menu({
					title:"ç‚¹æ­¤é€‰æ‹©æ¸¸æˆ",
					data:$.map($("#gameid option"),function(n){ return {text:$(n).text(),value:$(n).val()}; }),
					width:240,
					confirm:false,
					call:function(v){
						$("#speedsearch").trigger("setGame",v).trigger("showServer");
					}
				});
			}
		}else{
			$("#speedsearch").trigger("setGame",$(this).attr("val"));
			if(!noload) $("#speedsearch").trigger("showServer");
		}
		return false;
	},hover:function(){
		$(this).toggleClass("mouseover");
	//é¦–å­—ç¬¦é€‰æ‹©
	}}).delegate("#speedsearch_char td",{click:function(e){
		if($(this).is(".focus")){
			$(this).removeClass("focus");
			if($(this).text().match(/[A-Z]/)){
				$("#speedsearch_char td.all").addClass("focus");
			}
		}else{
			$("#speedsearch_char td").not($(this).addClass("focus")).removeClass("focus");
		}
		$("#speedsearch").trigger("showServer");
	},hover:function(){
		$(this).toggleClass("mouseover");
	}}).delegate("#speedsearch_result div.list",{hover:function(){
		$(this).toggleClass("mouseover");
	}});
    if(_ARGV.showserver){
        $("#speedsearch").trigger("showServer");
    }
	//æœåŠ¡å™¨ç­›é€‰
	$("#pagerule,#startquantity,#endquantity").keysave(function(){
		u_c_list();
	});
	$("#tab .content>div").hide();
	$("#tab .title>div").slice(1).on({
		"opentab":function(){
			var $con = $("#tab .content>div").eq($("#tab .title>div").index(this));
			if($con.length>0){
				$("#tab .title>div").not($(this).addClass("focus")).removeClass("focus")
				$("#tab .content>div").not($con.show()).hide();
			}
			if($(this).text().indexOf("æ›´æ–°")!=-1){			//è‡ªåŠ¨æ›´æ–°æŠ¥è­¦ä»·é‡
				u_g_list();
			}else if($(this).text().indexOf("è¿‡æ»¤")!=-1){	//è¿‡æ»¤åå•
				u_f_list();
			}
		},"click":function(){
			$(this).trigger("opentab");
		}
	}).hoverDelay({
		time:300,
		hoverEvent:function(){
			$(this).trigger("click");
		}
	}).filter(":first").trigger("opentab");
	$("#jquery_jplayer").jPlayer({
		swfPath:"/statics/javascripts/",
		ready:function(){
			this.element.jPlayer("setFile","/statics/sounds/focus.mp3");
		}
	});
	$.message_box({width:350,title:"å½“å‰æ— æŠ¥è­¦æœåŠ¡å™¨<a href='#stock'>åŽ»åº“å­˜è¡¨â†‘</a>/<a href='#top'>åŽ»é€ŸæŸ¥â†‘</a>"});
	$("#remarkdiv")
	.bind({show:function(e,$tr){
		var _op = $("[name=option]",$tr).val();
		$("#remarkdiv :button").each(function(i,v){
			_op.indexOf($(this).attr("name"))!=-1?$(this).show():$(this).hide();
		});
		if($tr.attr("hostid")==""){
			return ;
		}else if($("[name=hostid]",this).val()==$tr.attr("hostid")){
			if($(this).is(":hidden")) $(this).show();
		}else{
			try{ $.$tr.trigger("reset"); }catch(e){}
			$.$tr = $tr;
			var $st = $("[name=quantity]",$tr).parent();
			$("[name=hostid]",this).val($tr.attr("hostid"));
			$("[name=price]",this).val($("[name=price]",$tr).val());
			$("[name=remark]",this).val($("[name=remark]",$tr).val()).trigger("focusout").trigger("keyup");
			$(this).show().css({width : 180,left : $st.offset().left-1,   top : $st.offset().top+$st.height()+4 }).use("bgiframe/",function(){
				$(this).bgiframe();
			});
		}
	},hide:function(e,$tr){
		$(this).hide();
	}});
	$("#remarkdiv :button").click(function(){
		$.$tr.trigger("submit",[$(this).attr("name")]);
	});
	$("#remarkdiv a[name=reset]").click(function(){
		$.$tr.trigger("reset");
	});
	$("#remarkdiv [name=price]").keyup(function(){
		$("[name=price]",$.$tr).val($(this).val());
	});
	$("#remarkdiv [name=remark]").keyup(function(e){
		if(e.keyCode==38 || e.keyCode==40)return false;
		var $this = $(this);
		var val   = $(this).val().match(/\.$/)?"":$(this).val();
		var html  = "";
		rowsremark.sort(function(a,b){
			if(val == ""){
				return a.pinyin.localeCompare(b.pinyin);
			}else{
				var a1 = (a.name.toUpperCase().indexOf(val.toUpperCase())!=-1?5:0)+(a.pinyin.toUpperCase().indexOf(val.toUpperCase())!=-1?5:0);
				var b1 = (b.name.toUpperCase().indexOf(val.toUpperCase())!=-1?5:0)+(b.pinyin.toUpperCase().indexOf(val.toUpperCase())!=-1?5:0);
				return a.pinyin.localeCompare(b.pinyin)<0?(a1+1>b1?-1:1):(a1>b1+1?-1:1);
			}
		});
		for(var i=0;i<rowsremark.length;i++){
			html += "<div>"+rowsremark[i].pinyin.substring(0,1)+"-<a href=javascript:; class='info' index='"+(i+1)+"'>"+rowsremark[i].name+"</a></div>";
		}
		html += "<a href='?action=coin.conf' target='_blank' style=float:right>ç‚¹æ­¤ä¿®æ”¹å’Œæ·»åŠ å¸¸ç”¨å¤‡æ³¨...</a>";
		$("#remarkdata").html(html)
			.find("a.info")
			.click(function(){
				$this.val($(this).text()).css("color","#000000").trigger("keyup");
			});
		$("[name=remark]",$.$tr).val($(this).val());
	}).keydown(function(e){
		if(e.keyCode==13){
			return false;
		}else if(e.keyCode==38){
			var $div = $("#remarkdata div.focus").length==0?$("#remarkdata").find("div:last"):$("#remarkdata").find("div.focus").removeClass("focus").prev("div");
			$(this).val($div.addClass("focus").find("a").text());
			return false;
		}else if(e.keyCode==40){
			var $div = $("#remarkdata").find("div.focus").length==0?$("#remarkdata").find("div:first"):$("#remarkdata").find("div.focus").removeClass("focus").next("div");
			$(this).val($div.addClass("focus").find("a").text());
			return false;
		}
	});
	//æ–¹å‘é”®é€‰
	$(document).keydown(function(e){
		if($(e.target).is(":input")){
			return true;
		}else{
			if(e.keyCode == 37 || e.keyCode == 38){
				u_c_next(lasthostid,-1);
				return false;
			}else if(e.keyCode == 39 || e.keyCode == 40){
				u_c_next(lasthostid,1);
				return false;
			}
		}
	//é¼ æ ‡æ”¾åœ¨ç½‘ç«™ä¸Šé¢çš„å°æ—¶æ•ˆæžœ
	}).delegate("a[_siteid]","hover",function(e){
		if(e.type == "mouseenter"){
			var _f  = $(this).offset();
			var _s  = $(this).attr("_siteid");
			_f.left += $(this).width();
			var _ht = '<div style="padding:10px;font-size:16px;font-weight:500">'+(_s<0?'æ‹…ä¿äº¤æ˜“å•†,æœ‰æŠ¼é‡‘æ‹…ä¿,å¯æ”¾å¿ƒå‡ºè´§ï¼':'éžæ‹…ä¿äº¤æ˜“è¯·è‡ªè¡Œè¯„ä¼°é£Žé™©ï¼Œæ¯”ä»·å™¨ä¸ä»‹å…¥çº çº·å¤„ç†')+'</div>';
			$.layer("float").show().css(_f).html(_ht);
		}else{
			$.layer("float").hide();
		}
	}).delegate("a[_siteid][_hostid]","click",function(e){
		$.get("index.php?action=site&hostid="+$(this).attr("_hostid")+"&siteid="+$(this).attr("_siteid")+"");
	}).delegate("a.oicq","click",function(e){
		$tr = $(this).closest("tr");
		$.get("index.php?action=oicq&hostid="+$tr.attr("_hostid"));
	}).delegate("a.host","click",function(){
		u_h_view($(this).closest(".data").attr("hostid"));
		return false;
	}).delegate("a.del","click",function(){
		var $tr = $(this).closest("tr.data");
		if($.intval($("[name=oldquantity]",$tr).val())==0){
			u_c_del($tr.attr("hostid"));
		}else{
			$("[name=price]",$tr).val($("[name=avgprice]",$tr).text());
			$("[name=quantity]",$tr).val(0);
			$("[name=inquantity]",$tr).val($("[name=oldquantity]",$tr).val());
			$("[name=option]",$tr).val("delete");
			$("[name=quantity]",$tr).trigger("input");
		}
	});
	$("#coinlist").delegate("tr.data",{mouseover:function(e){
		$(this).addClass("mouseover");
	},mouseout:function(){
		$(this).removeClass("mouseover");
	},click:function(){
		$("#coinlist tr.data.focus").removeClass("focus");
		$(this).addClass("focus");
	},input:function(e){
		var $tr = $(this);
		if($("[name=inquantity]",$tr).val()==""){
			$("#remarkdiv").trigger("hide",[$tr]);
		}else{
			if($("[name=price]",$tr).val()=="") $("[name=price]",$tr).val($("[name=avgprice]",$tr).text());
			$("#remarkdiv").trigger("show",[$tr]);
		}
	},reset:function(){
		var $tr = $(this);
		$("[name=option],[name=inquantity],[name=price],[name=remark]",$tr).val("");
		$("[name=quantity]",$tr).val($("[name=oldquantity]",$tr).val());
		$tr.trigger("input");
	},submit:function(e,option){
		var $tr   = $.$tr;
		var $td   = $("td.excel:has([name=quantity])",$tr);
		if(option=="out" && $.intval($("[name=inquantity]",$tr).val())>$.intval($("[name=oldquantity]",$tr).val())){
			alert("å‡ºåº“æ•°é‡"+$("[name=inquantity]",$tr).val()+"ä¸èƒ½å¤§äºŽä½ å½“å‰åº“å­˜é‡"+$("[name=oldquantity]",$tr).val());
		}else{
			$.layer("showdiv")
				.html(msg_proce)
				.show()
				.css({left:$td.offset().left+$td.width(),top:$td.offset().top});
			$.post("?action=coin.rowsadd&hostid="+$tr.attr("hostid")+"&method="+option,$("input",$tr).serialize(),function(d){
				$.layer("showdiv").html(msg_success).fadeOut(1500);
				if(d.errno==0){
					if($("#fasthostname",$tr).length>0){
						$("input",$tr).val("");
					}
					$tr = $("#data_"+$tr.attr("hostid"));
					if($tr.length == 0){
						u_c_list();
						$("#remarkdiv").trigger("hide");
					}else if(option=="delete"){
						$tr.trigger("reset");
						u_c_del($tr.attr("hostid"));
					}else{
						$tr.trigger("reset");
						$("[name=quantity]",$tr).val(d.quantity);
						$("[name=oldquantity]",$tr).val(d.quantity);
						$("[name=maxprice]",$tr).val(d.maxprice);
						$("[name=maxquantity]",$tr).val(d.maxquantity);
						$("[name=avgprice]",$tr).html(d.avgprice);
					}
				}else{
					alert(d.error);
				}
			},"json");
		}
	}}).delegate("tr.data :input",{keydown:function(e){
		if(e.keyCode==9 && ($(this).attr("name")=="quantity" || $(this).attr("name")=="inquantity")){
			$("#remarkdiv [name=price]").focus().trigger("focusin");
			return false;
		}else{
			return true;
		}
	},"keyup":function(e){
		var _h    = Math.random();
		var _name = $(this).attr("name");
		var $td   = $(this).closest("td");
		var $tr   = $(this).closest("tr.data");
		var $this = $(this).attr("_h",_h);
		if(_name.match(/quantity|price/) && $this.val().match(/[^\d\.]=/)){
			$this.val($this.val().replace(/[^\d\.]+/,''));
		}
		//è‡ªåŠ¨ä¿å­˜æŠ¥è­¦è®¾ç½®
		if(_name.match(/(maxprice|maxquantity|quantity|price|description|summary)/)){
			if(_name == "quantity"){
				var quantity = $.intval($this.val())-$.intval($("[name=oldquantity]",$tr).val());
				//æ•°é‡è®¡ç®—
				if(quantity==0){
					$("[name=inquantity]",$tr).val("");
				}else if(quantity>0){
					//åªæ˜¾ç¤ºä¿å­˜æŒ‰é’®
					$("[name=option]",$tr).val("in");
					$("[name=inquantity]",$tr).val(quantity);
				}else{
					//åªæ˜¾ç¤ºä¿å­˜æŒ‰é’®
					$("[name=option]",$tr).val("out");
					$("[name=inquantity]",$tr).val(quantity*-1);
				}
			}else if(_name == "inquantity"){
				$("[name=quantity]",$tr).val($("[name=oldquantity]",$tr).val());
				//æ˜¾ç¤ºå…¥åº“å’Œå‡ºåº“æŒ‰é’®
				$("[name=option]",$tr).val("in,out");
			}else if(_name=="price"){
				$("#remarkdiv [name=price]").val($(this).val());
			}else{
				setTimeout(function(){
					if(_h == $this.attr("_h")){
						$.layer("showdiv")
							.html(msg_proce)
							.show()
							.css({left:$this.offset().left+50,top:$this.offset().top});
						u_c_set($this.closest("tr.data").attr("hostid"),$this.attr("name"),$this.val());
					}
				},800);
				return ;
			}
		}
		$tr.trigger("input");
	},focusin:function(){
		var $tr   = $(this).closest("tr.data");
		if($(this).val()=="0"){
			$(this).attr("zero",msg_success).val("");
		}
		if($(this).is("[name=description]") || $(this).is("[name=summary]")){
			$(this).attr("_height",$(this).height()).height(100);
		}
		$tr.trigger("input");
	},focusout:function(){
		var $tr   = $(this).closest("tr.data");
		if($(this).val()==""){
			if($(this).attr("zero")==msg_success) $(this).val("0");
		}
		if($(this).is("[name=description]") || $(this).is("[name=summary]")){
			$(this).height($(this).attr("_height"));
		}
		$tr.trigger("input");
	}}).delegate("a.last","click",function(){
		var $tr    = $(this).closest("tr");
		var $layer = $.layer("last",{type:"box",width:494}).show().css({left:$tr.offset().left,top:$tr.offset().top+$tr.height()});
		$(".title",$layer).hide();
		$(".content",$layer).load("?action=coin.rowslast&hostid="+$tr.attr("hostid"));
	}).delegate("tr.last :input",{save:function(e){
		var $tr   = $(this).closest("tr");
		var $this = $(this);
		$.layer("showdiv")
			.html(msg_proce)
			.show()
			.css({left:$this.offset().left+50,top:$this.offset().top});
		$.post("?action=coin.rowsset",{rowsid:$tr.attr("rowsid"),name:$(this).attr("name"),value:$(this).val()},function(d){
			if(d.errno!=0){
				alert(d.error);
			}
			$.layer("showdiv").html(msg_success).fadeOut(1500);
		},"json");
	},change:function(){
		if($(this).is("select")) $(this).trigger("save");
	},keyup:function(e){
		var _h    = Math.random();
		var $this = $(this).attr("_h",_h);
		var $tr   = $this.closest("tr");
		setTimeout(function(){
			if(_h == $this.attr("_h")){
				$this.trigger("save");
			}
		},800);
	}});
	$("#gameid").wSelect({ cols:5,width:800,maxLength:18,historyName:"HG"}).trigger("change");
//	$("#hostid").wSelect({ cols:6,width:800,maxLength:20,historyName:"HH",clickClose:true});
	/* ç”¨æˆ·é»˜è®¤æ•°æ® */
    if(_ARGV.serverid!="0"){         /*è¯»å–é»˜è®¤æœåŠ¡å™¨*/
        setTimeout(function(){
            u_h_view(_ARGV.serverid);
        },1000);
    }else if(_ARGV.lastgameid!="0"){ /*æœ€åŽé€‰æ‹©çš„æ¸¸æˆID*/
        $("#gameid").val(_ARGV.lastgameid).trigger("change");
    }
    $("#speedsearch").trigger('setGame',_ARGV.lastfastgameid!="0"?_ARGV.lastfastgameid:10).trigger("showServer");
});