var page = require('webpage').create(),
    system = require('system'),
    fs = require('fs'),
    address;
var weibo_userid = system.args[1]
var weibo_passwd = system.args[2]
var startUrl = "https://api.weibo.com/oauth2/authorize?client_id=204574897&redirect_uri=www.renren.com/yuanpuhao&response_type=token";
var verify_weibo_freeze = false;
page.onResourceReceived = function (res,network) {
    if (res.stage == "end") {
        // console.log("\t<-" + res.url);
        if (res.url.indexOf("authorize?client_id")>0) {
            startUrl = res.url
        } 
        if (res.url.indexOf("?access_token")>0) {
            var pos1 = res.url.indexOf("access_token=")
            var pos2 = res.url.indexOf("&")
            var access_token = res.url.substring(pos1+"access_token=".length, pos2)
            console.log(weibo_userid + " login OK, access_token is: " + access_token)
            verify_weibo_freeze = true
        }
        if (verify_weibo_freeze && res.url != "http://weibo.com/" && res.url.indexOf("http://weibo.com/")>-1) {
            var pos1 = res.url.indexOf("/",8)
            var pos2 = res.url.indexOf("?")
            var weibo_name = res.url.substring(pos1+1,pos2)
            console.log(weibo_name+" status verified OK")
            phantom.exit();
        }
    }
};
page.onLoadFinished = function() {
    if (verify_weibo_freeze) {
        page.open("http://weibo.com/", function() {
            phantom.exit();
        })
    }
};
page.onConsoleMessage = function(msg) {
    console.log(msg);
};
page.open(startUrl, function(status) {
    if ( status === "success" ) {
        page.includeJs("https://ajax.googleapis.com/ajax/libs/jquery/1.6.1/jquery.min.js", function() {
            var offset = page.evaluate(function(a,b) {
                $("#userId").val(a)
                $("#passwd").val(b)
                if ($('.WB_btn_login').hasClass("formbtn_01")) {
                    // console.log("Found button!")
                    return $('.WB_btn_login').offset()
                }
                return undefined
            }, weibo_userid, weibo_passwd);
            page.sendEvent('click', offset.left + 1, offset.top + 1);
        });
    }
})