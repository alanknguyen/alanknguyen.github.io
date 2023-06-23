const sections = document.querySelectorAll('section');
const navItems = document.querySelectorAll('#navbar a');

const observer = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const id = entry.target.getAttribute('id');
      const navItem = document.querySelector(`#navbar a[href="#${id}"]`);
      
      navItems.forEach(item => {
        item.parentNode.classList.remove('active');
      });

      if(navItem) {
        navItem.parentNode.classList.add('active');
      }
    }
  });
}, { threshold: 0.5 });  // Threshold means at least 50% of the section is in viewport

sections.forEach(section => {
  observer.observe(section);
});


document.getElementById('contact-form').addEventListener('submit', function(event) {
    event.preventDefault(); // prevent the form from submitting normally

    var name = document.getElementById('name').value;
    var email = document.getElementById('email').value;
    var note = document.getElementById('note').value;

    console.log('Name: ' + name);
    console.log('Email: ' + email);
    console.log('Note: ' + note);
});
