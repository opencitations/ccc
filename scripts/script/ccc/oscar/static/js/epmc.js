function loadedContent() {
  var cited = window.location.href.substring(window.location.href.lastIndexOf('/') - 2);
  console.log(cited);
  $("a.res-val-link").each(
      function() {
        alert("hi");
      }
  );
  return true
};

// $(document).ready(function() {
//   // CCC
//
//
//     // var cited = window.location.href.substring(window.location.href.lastIndexOf('/') - 2);
//     // console.log(cited);
//     // console.log("oscar active");
//     //
//     // if (($("li#oscar_menu_0").filter("[class='active']")) && ($("li#oscar_menu_0 a[href~='doc_cites_me_list']"))) {
//     //     if ($("td[field='mentions'] > a") != undefined) {
//     //         $("td[field='mentions'] > a").each(
//     //             function() {
//     //               console.log($(this).attr("href"));
//     //             }
//     //         );
//     //     };
//     // };
//
// });
