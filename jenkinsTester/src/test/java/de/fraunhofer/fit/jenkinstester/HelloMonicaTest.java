package de.fraunhofer.fit.jenkinstester; /**
 * Created by devasya on 29.06.2017.
 */

import junit.framework.TestCase;

public class HelloMonicaTest extends TestCase {
    protected HelloMonica helloMonica;
    protected void setUp(){
        helloMonica = new HelloMonica();
    }


    public void testhelloMonica() {
        assertEquals(helloMonica.helloMonica(),"Hello, Monica!!");
    }
}
